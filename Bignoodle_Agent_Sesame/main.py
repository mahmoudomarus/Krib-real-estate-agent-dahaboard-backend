import logging
import queue
import threading
import time
import numpy as np
import sounddevice as sd
import yaml # For config loading
# from dotenv import load_dotenv # For .env loading
import os
from typing import List, Dict

# Import custom modules
from src.stt_module import SpeechToText
from src.llm_module import LanguageModel
from src.tts_module import TextToSpeech

# TODO: Import chosen VAD library based on config[\'audio\'][\'vad_implementation\']
# Example for Silero:
# import torch
# if config[\'audio\'][\'vad_implementation\'] == \'silero\':
#     try:
#         # torch.set_num_threads(1) # Consider setting globally if needed
#         vad_model, vad_utils = torch.hub.load(repo_or_dir=\'snakers4/silero-vad\',
#                                             model=\'silero_vad\',
#                                             force_reload=False) 
#         (get_speech_timestamps,
#         save_audio,
#         read_audio,
#         VADIterator,
#         collect_chunks) = vad_utils
#         logger.info("Silero VAD model loaded.")
#     except Exception as e:
#         logger.exception(f"Error loading Silero VAD model: {e}")
#         vad_model = None
# else: # Add other VAD implementations here
#     vad_model = None
#     VADIterator = None # Ensure VADIterator is defined or None


# --- Configuration Loading ---
# load_dotenv() 
CONFIG_PATH = os.getenv("CONFIG_PATH", "config/config.yaml")
try:
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    logger.info(f"Configuration loaded from {CONFIG_PATH}")
except FileNotFoundError:
    logger.error(f"Configuration file not found at {CONFIG_PATH}. Exiting.")
    exit(1)
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    exit(1)

# --- Logging Setup ---
log_level = config.get('log_level', 'INFO').upper()
logging.basicConfig(level=log_level, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info(f"Log level set to {log_level}")


# --- Calculate derived audio settings ---
SAMPLE_RATE = config['audio']['sample_rate']
CHUNK_DURATION_MS = config['audio']['chunk_duration_ms']
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION_MS / 1000)
logger.info(f"Audio Settings: Sample Rate={SAMPLE_RATE}Hz, Chunk Size={CHUNK_SIZE} frames ({CHUNK_DURATION_MS}ms)")

# --- Global State & Queues ---
audio_queue = queue.Queue() # Queue for raw audio chunks from mic
speech_buffer = []          # Buffer to hold detected speech chunks
is_speaking = False         # Flag indicating if the user is currently speaking (detected by VAD)
is_agent_speaking = False   # Flag indicating if the agent is currently playing TTS audio
last_speech_time = time.time()
conversation_history = []   # Store conversation turns: [{\'role\': \'user\', \'content\': \'...\'}, ...]
processing_thread = None    # Thread for handling the STT->LLM->TTS pipeline
shutdown_event = threading.Event() # Event to signal threads to stop

# --- Module Initialization ---
try:
    logger.info("Initializing STT module...")
    # TODO: Potentially select STT class based on config[\'stt\'][\'implementation\']
    stt_model = SpeechToText(
        model_path=config['stt']['model_path'],
        device=config['stt']['device'],
        compute_type=config['stt']['compute_type']
        # Add other params like batch_size if needed from config['stt']
    )
    
    logger.info("Initializing LLM module...")
    llm_engine = config['llm']['engine']
    llm_kwargs = config['llm'].get('engine_kwargs', {})
    llm_model = LanguageModel(
        model_path=config['llm']['model_path'],
        engine=llm_engine,
        device=config['llm']['device'],
        **llm_kwargs # Pass engine-specific kwargs
    )
    
    logger.info("Initializing TTS module...")
    # TODO: Potentially select TTS class based on config['tts']['implementation']
    tts_model = TextToSpeech(
        model_path=config['tts']['model_path'],
        device=config['tts']['device']
        # Add other params like speaker_id if needed from config['tts']
    )
    
    logger.info("Initializing VAD module...")
    if config['audio']['vad_implementation'] == 'silero' and 'VADIterator' in locals() and VADIterator is not None:
         vad_iterator = VADIterator(vad_model, threshold=config['audio']['vad_threshold'])
         logger.info(f"Using Silero VAD with threshold {config['audio']['vad_threshold']}.")
    else:
         # TODO: Implement initialization for other VAD types or handle no VAD
         logger.warning(f"VAD implementation '{config['audio']['vad_implementation']}' not fully configured or loaded. Using basic volume check.")
         vad_iterator = None # Fallback placeholder

except Exception as e:
    logger.exception(f"Failed to initialize models: {e}")
    exit(1)

# --- Audio Callback ---
def audio_callback(indata, frames, time_info, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        logger.warning(f"Audio callback status: {status}")
    if not shutdown_event.is_set():
        audio_queue.put(indata.copy()) # Put audio chunk into the queue

# --- VAD & Processing Logic ---
def process_audio_stream():
    global is_speaking, last_speech_time, speech_buffer, processing_thread, is_agent_speaking

    logger.info("Audio processing thread started.")
    min_silence_duration_s = config['audio']['silence_duration_ms'] / 1000.0
    min_silence_chunks = int(min_silence_duration_s * SAMPLE_RATE / CHUNK_SIZE)
    max_speech_duration_s = config['audio']['max_speech_duration_s']
    max_speech_chunks = int(max_speech_duration_s * SAMPLE_RATE / CHUNK_SIZE)
    vad_threshold = config['audio']['vad_threshold']
    silence_counter = 0

    while not shutdown_event.is_set():
        try:
            audio_chunk = audio_queue.get(timeout=0.1) # Wait briefly for audio
            
            is_currently_speech = False
            if vad_iterator:
                # TODO: Actual Silero VAD usage - API might differ slightly
                # Ensure audio_chunk is in the correct format (e.g., Float32 Tensor for Silero)
                # Example:
                # audio_float32 = torch.from_numpy(audio_chunk).float()
                # speech_dict = vad_iterator(audio_float32, return_seconds=False) # Check API
                # if speech_dict and 'speech' in speech_dict:
                #    is_currently_speech = True
                # Implement actual VAD logic here based on chosen library
                volume_norm = np.linalg.norm(audio_chunk) * 10 # Placeholder if VAD fails
                is_currently_speech = min(1.0, volume_norm) > vad_threshold # Placeholder
                pass # Remove pass when VAD logic is implemented
            else:
                # Fallback VAD logic (basic volume check)
                volume_norm = np.linalg.norm(audio_chunk) * 10
                is_currently_speech = min(1.0, volume_norm) > vad_threshold
            
            # --- Interruption / Speech Handling ---
            if is_currently_speech:
                if is_agent_speaking:
                    # --- Interruption Logic ---
                    logger.info("User interruption detected!")
                    sd.stop() # Stop TTS playback immediately
                    is_agent_speaking = False 
                    # Clear the buffer and reset silence counter to immediately process interruption
                    speech_buffer = [audio_chunk] # Start buffer with the interrupting chunk
                    silence_counter = 0
                    is_speaking = True # User is now speaking
                    last_speech_time = time.time()
                    # Optional: Could signal the processing_thread to stop if needed, but might be complex.
                    # For now, let the old response finish generating in the background if it hasn't played.
                elif not is_speaking:
                    logger.debug("Speech start detected.")
                    is_speaking = True
                    speech_buffer = [audio_chunk] # Start buffer
                    silence_counter = 0
                    last_speech_time = time.time()
                else:
                    # Continue ongoing user speech
                    speech_buffer.append(audio_chunk)
                    last_speech_time = time.time()
                    silence_counter = 0 # Reset silence counter while speech continues

                # Force processing if speech is too long
                if is_speaking and len(speech_buffer) > max_speech_chunks:
                    logger.warning(f"Maximum speech duration ({max_speech_duration_s}s) reached. Forcing processing.")
                    if not (processing_thread and processing_thread.is_alive()):
                        process_user_speech(list(speech_buffer)) # Process current buffer
                    # Reset state after forcing process
                    speech_buffer = [] 
                    is_speaking = False
                    silence_counter = 0
            
            # --- Silence Handling ---
            else: # Not speech
                if is_speaking:
                    silence_counter += 1
                    if silence_counter >= min_silence_chunks:
                        logger.debug(f"End of speech detected by silence ({min_silence_duration_s:.2f}s).")
                        if speech_buffer and not (processing_thread and processing_thread.is_alive()):
                            process_user_speech(list(speech_buffer))
                        # Reset state after silence triggers processing
                        speech_buffer = [] 
                        is_speaking = False
                        silence_counter = 0
                # else: User is not speaking, and wasn't speaking before - do nothing

            # Reset VAD state if the specific library requires it (e.g., vad_iterator.reset_states())

        except queue.Empty:
            # Timeout handling: Check if user was speaking but stopped abruptly
            if is_speaking and (time.time() - last_speech_time) > min_silence_duration_s:
                 logger.debug(f"End of speech detected by timeout ({min_silence_duration_s:.2f}s).")
                 if speech_buffer and not (processing_thread and processing_thread.is_alive()):
                     process_user_speech(list(speech_buffer))
                 # Reset state after timeout triggers processing
                 speech_buffer = [] 
                 is_speaking = False
                 silence_counter = 0
            continue
        except Exception as e:
            logger.exception(f"Error in audio processing loop: {e}")
            time.sleep(0.1)

    logger.info("Audio processing thread finished.")


def process_user_speech(audio_chunks: List[np.ndarray]):
    """Handles the STT -> LLM -> TTS pipeline in a separate thread."""
    global processing_thread
    processing_thread = threading.Thread(target=run_inference_pipeline, args=(audio_chunks,))
    processing_thread.start()

def run_inference_pipeline(audio_chunks: List[np.ndarray]):
    """The function executed in the processing thread."""
    global conversation_history, is_agent_speaking
    
    if not audio_chunks:
        logger.warning("Tried to process empty audio buffer.")
        return

    logger.info(f"Processing {len(audio_chunks) * CHUNK_DURATION_MS / 1000.0:.2f}s of user audio...")
    try:
        # Concatenate audio chunks
        full_audio = np.concatenate(audio_chunks).flatten() # Ensure 1D array
        
        # 1. Speech-to-Text
        start_stt = time.time()
        user_text = stt_model.transcribe_audio(full_audio, SAMPLE_RATE)
        stt_latency = time.time() - start_stt
        logger.info(f"STT ({stt_latency:.2f}s): {user_text}")

        if not user_text or user_text.strip().lower() in ["", "okay", "thanks", "thank you", "bye", "goodbye"]: # Basic filtering
            logger.info("Skipping LLM/TTS due to short/non-substantive/exit transcription.")
            # Consider adding a simple canned response for exit phrases
            return

        # --- History Management ---
        current_turn = {"role": "user", "content": user_text}
        # Keep only the last N turns for context
        max_turns = config.get('max_history_turns', 10)
        effective_history = conversation_history[-(max_turns - 1):] if max_turns > 0 else []
        
        # Add current user message to history for LLM
        history_for_llm = effective_history + [current_turn]

        # 2. Language Model
        start_llm = time.time()
        llm_gen_params = config['llm'].get('generation', {})
        agent_text = llm_model.generate_response(
            prompt=user_text, # Might not be needed if history format includes last user turn
            history=history_for_llm, # Pass formatted history
            **llm_gen_params # Pass generation params like max_tokens, temp, etc.
        )
        llm_latency = time.time() - start_llm
        logger.info(f"LLM ({llm_latency:.2f}s): {agent_text}")
        
        # --- Update Conversation History ---
        # Add user turn (already done for LLM input prep)
        conversation_history.append(current_turn)
        # Add assistant turn
        conversation_history.append({"role": "assistant", "content": agent_text})
        # Trim history overall to max_turns (including the latest assistant response)
        conversation_history = conversation_history[-max_turns:] if max_turns > 0 else []
        logger.debug(f"History updated. Turns: {len(conversation_history)}")


        # 3. Text-to-Speech
        start_tts = time.time()
        # TODO: Check if TTS model provides sample rate or use config
        tts_output_sample_rate = config['tts'].get('sample_rate', 24000) # Placeholder
        agent_audio, actual_tts_sample_rate = tts_model.synthesize_speech(agent_text)
        # Use actual sample rate if returned, otherwise config/default
        tts_sample_rate = actual_tts_sample_rate if actual_tts_sample_rate > 0 else tts_output_sample_rate 
        tts_latency = time.time() - start_tts
        if agent_audio is not None and agent_audio.size > 0:
             audio_duration = len(agent_audio)/tts_sample_rate
             logger.info(f"TTS ({tts_latency:.2f}s): Generated {audio_duration:.2f}s of audio at {tts_sample_rate}Hz.")
        else:
             logger.warning(f"TTS ({tts_latency:.2f}s): Failed to generate audio.")


        # 4. Playback
        if agent_audio is not None and agent_audio.size > 0:
            # Check shutdown event *before* starting playback
            if shutdown_event.is_set():
                logger.info("Shutdown signalled before TTS playback could start.")
                return
                
            is_agent_speaking = True # Set flag RIGHT before starting playback
            logger.info("Starting TTS playback...")
            playback_start_time = time.time()
            try:
                sd.play(agent_audio, tts_sample_rate, 
                        device=config['audio']['output_device_index'],
                        blocking=True) # Play synchronously
                # Blocking ensures is_agent_speaking remains True until done/stopped.
                logger.info(f"TTS playback finished naturally ({time.time() - playback_start_time:.2f}s).")
                
                # --- Post-playback Delay ---
                delay_ms = config['audio'].get('post_playback_delay_ms', 0)
                if delay_ms > 0:
                    logger.debug(f"Applying post-playback delay: {delay_ms}ms")
                    time.sleep(delay_ms / 1000.0)

            except sd.PortAudioError as pae:
                 # Handle potential device errors during playback
                 logger.error(f"SoundDevice playback error: {pae}")
                 # Maybe try stopping again?
                 sd.stop()
            except Exception as e:
                logger.exception(f"Error during TTS playback: {e}")
                 # Ensure stop is called on unexpected errors too
                 sd.stop()
            finally:
                 # **Critical**: Ensure flag is ALWAYS reset after playback attempt finishes or fails
                 # This happens *after* the blocking play() finishes or is interrupted/errors out.
                 logger.debug(f"Resetting is_agent_speaking flag. Current value: {is_agent_speaking}")
                 is_agent_speaking = False
        else:
            logger.warning("Skipping playback as TTS did not produce audio.")
            # Ensure flag is false if no audio was generated
            is_agent_speaking = False

    except Exception as e:
        logger.exception(f"Error in inference pipeline: {e}")
    finally:
         # Final fallback check to ensure the flag is reset if an error occurred *before* playback block
         if is_agent_speaking: # If flag was somehow left true due to early exit
             logger.warning("Resetting is_agent_speaking flag in final exception handler.")
             is_agent_speaking = False

# --- Main Execution ---
if __name__ == "__main__":
    logger.info("Starting Voice Agent...")
    
    audio_processor_thread = threading.Thread(target=process_audio_stream)
    
    try:
        # Start the audio stream
        stream = sd.InputStream(
            callback=audio_callback,
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            device=config['audio']['input_device_index']
        )
        stream.start()
        logger.info(f"Microphone stream started on device {stream.device} with samplerate {stream.samplerate}Hz and blocksize {stream.blocksize}.")
        
        # Start the VAD processing thread
        audio_processor_thread.start()
        
        # Keep the main thread alive, listening for KeyboardInterrupt
        while not shutdown_event.is_set():
            # Check if threads are alive periodically (optional)
            if not audio_processor_thread.is_alive():
                logger.error("Audio processing thread unexpectedly died. Shutting down.")
                break # Exit loop to trigger shutdown
            # Check if processing thread got stuck (optional, needs care)
            # if processing_thread and processing_thread.is_alive():
                # Add logic to check if it's been running too long? Difficult.
            time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received (KeyboardInterrupt).")
    except sd.PortAudioError as pae:
        logger.exception(f"SoundDevice stream error: {pae}. Try checking device indices and sample rates.")
    except Exception as e:
        logger.exception(f"An error occurred in the main loop: {e}")
    finally:
        logger.info("Shutting down...")
        shutdown_event.set() # Signal threads to stop
        
        # Stop and close the audio stream first
        if 'stream' in locals() and stream.active:
            try:
                stream.stop()
                stream.close()
                logger.info("Microphone stream stopped and closed.")
            except sd.PortAudioError as pae:
                logger.error(f"Error stopping/closing audio stream: {pae}")
            except Exception as e:
                logger.error(f"Unexpected error closing stream: {e}")
        else:
            logger.info("Microphone stream was not active or already closed.")
            
        # Stop any potential leftover playback 
        # Doing this after stream close might be cleaner sometimes
        try:
            sd.stop()
            logger.info("Ensured any active playback is stopped.")
        except sd.PortAudioError as pae:
            logger.error(f"Error stopping playback during shutdown: {pae}")
        except Exception as e:
            logger.error(f"Unexpected error stopping playback: {e}")

        # Join threads after signalling stop and closing resources
        if audio_processor_thread.is_alive():
             logger.info("Joining audio processor thread...")
             audio_processor_thread.join(timeout=2) 
             if audio_processor_thread.is_alive():
                 logger.warning("Audio processor thread did not exit cleanly.")
             else:
                 logger.info("Audio processor thread joined.")

        if processing_thread and processing_thread.is_alive():
             logger.info("Joining inference thread (if running)...")
             # Add a mechanism here to signal the inference thread itself if possible.
             # For now, just join with timeout.
             processing_thread.join(timeout=5) 
             if processing_thread.is_alive():
                 logger.warning("Inference thread did not exit cleanly (might be stuck in model call).")
             else:
                 logger.info("Inference thread joined.")

        logger.info("Voice Agent shut down complete.") 