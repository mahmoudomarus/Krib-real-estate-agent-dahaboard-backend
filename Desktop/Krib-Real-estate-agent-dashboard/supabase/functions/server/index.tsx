import { Hono } from "npm:hono";
import { cors } from "npm:hono/cors";
import { logger } from "npm:hono/logger";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import * as kv from "./kv_store.tsx";
import {
  initializeStorage,
  uploadPropertyImage,
  deletePropertyImage,
  getPropertyImages,
} from "./file-upload.tsx";

const app = new Hono();

app.use("*", logger(console.log));
app.use(
  "*",
  cors({
    origin: "*",
    allowHeaders: ["*"],
    allowMethods: ["*"],
  }),
);

const supabase = createClient(
  Deno.env.get("SUPABASE_URL")!,
  Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,
);

// Initialize storage on startup
initializeStorage();

// Create demo user for testing (DISABLED for production)
async function createDemoUser() {
  // PRODUCTION: Demo user creation disabled
  console.log("Demo user creation is disabled in production");
  return;
  try {
    // Check if demo user already exists in Supabase Auth
    const { data: existingUsers } =
      await supabase.auth.admin.listUsers();
    const demoExists = existingUsers?.users?.some(
      (user) => user.email === "demo@rentalai.com",
    );

    if (!demoExists) {
      console.log("Creating demo user in Supabase Auth...");
      const { data, error } =
        await supabase.auth.admin.createUser({
          email: "demo@rentalai.com",
          password: "demo123",
          user_metadata: { name: "Demo User" },
          email_confirm: true,
        });

      if (error) {
        console.log("Demo user creation error:", error);
        return;
      }

      console.log(
        "Demo user created successfully in Supabase Auth:",
        data.user.id,
      );

      // Store demo user profile in KV store
      const profile = {
        id: data.user.id,
        name: "Demo User",
        email: "demo@rentalai.com",
        createdAt: new Date().toISOString(),
        properties: [],
        totalRevenue: 0,
        settings: {
          notifications: {
            bookings: true,
            marketing: false,
            systemUpdates: true,
          },
          preferences: {
            currency: "USD",
            timezone: "America/New_York",
            language: "English",
          },
        },
      };

      await kv.set(`user:${data.user.id}:profile`, profile);

      // Create sample properties for demo user
      const sampleProperties = [
        {
          title: "Modern Downtown Apartment",
          address: "123 Main St, Downtown",
          propertyType: "apartment",
          bedrooms: 2,
          bathrooms: 2,
          maxGuests: 4,
          pricePerNight: 150,
          description:
            "Beautiful modern apartment in the heart of downtown with stunning city views.",
          amenities: [
            "WiFi",
            "Kitchen",
            "Air Conditioning",
            "Parking",
          ],
        },
        {
          title: "Cozy Beach House",
          address: "456 Ocean Ave, Beachfront",
          propertyType: "house",
          bedrooms: 3,
          bathrooms: 2,
          maxGuests: 6,
          pricePerNight: 280,
          description:
            "Charming beach house just steps from the ocean with private deck.",
          amenities: [
            "WiFi",
            "Kitchen",
            "Beach Access",
            "Deck",
            "Parking",
          ],
        },
      ];

      for (let i = 0; i < sampleProperties.length; i++) {
        const propertyData = sampleProperties[i];
        const propertyId = crypto.randomUUID();
        const property = {
          id: propertyId,
          userId: data.user.id,
          ...propertyData,
          images: [],
          status: "active",
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          bookings: Math.floor(Math.random() * 15) + 5,
          revenue: Math.floor(Math.random() * 5000) + 2000,
          rating: 4.5 + Math.random() * 0.4,
          reviews: Math.floor(Math.random() * 20) + 10,
        };

        await kv.set(`property:${propertyId}`, property);
        profile.properties.push(propertyId);
      }

      // Update profile with property IDs
      await kv.set(`user:${data.user.id}:profile`, profile);
      console.log(
        "Demo user and sample properties created successfully",
      );

      // Create sample bookings for demo properties
      const sampleBookings = [
        {
          property: "Modern Downtown Apartment",
          propertyId: profile.properties[0],
          guest: {
            name: "John Smith",
            email: "john.smith@email.com",
            phone: "+1-555-0123",
          },
          checkIn: "2024-01-15",
          checkOut: "2024-01-18",
          nights: 3,
          guests: 2,
          amount: 450,
          status: "confirmed" as const,
          specialRequests: "Late check-in requested",
        },
        {
          property: "Cozy Beach House",
          propertyId: profile.properties[1],
          guest: {
            name: "Sarah Johnson",
            email: "sarah.johnson@email.com",
            phone: "+1-555-0456",
          },
          checkIn: "2024-01-22",
          checkOut: "2024-01-26",
          nights: 4,
          guests: 4,
          amount: 1120,
          status: "pending" as const,
          specialRequests: "Pet-friendly accommodation needed",
        },
        {
          property: "Modern Downtown Apartment",
          propertyId: profile.properties[0],
          guest: {
            name: "Mike Wilson",
            email: "mike.wilson@email.com",
            phone: "+1-555-0789",
          },
          checkIn: "2024-02-01",
          checkOut: "2024-02-03",
          nights: 2,
          guests: 1,
          amount: 300,
          status: "confirmed" as const,
        },
      ];

      // Create the sample bookings
      for (const bookingData of sampleBookings) {
        const bookingId =
          "BK" +
          Date.now().toString() +
          Math.random().toString(36).substr(2, 5);
        const booking = {
          id: bookingId,
          ...bookingData,
          bookingDate: new Date().toISOString(),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };

        await kv.set(`booking:${bookingId}`, booking);
      }

      console.log("Demo bookings created successfully");
    } else {
      console.log("Demo user already exists in Supabase Auth");
    }
  } catch (error) {
    console.log("Demo user setup error:", error);
  }
}

// Initialize demo user (DISABLED for production)
// createDemoUser();

// Enhanced error handler
function handleError(error: any, context: string) {
  const timestamp = new Date().toISOString();
  const errorMessage = error?.message || "Unknown error";
  const stack = error?.stack || "No stack trace";

  console.error(`[${timestamp}] ${context}:`, {
    message: errorMessage,
    stack: stack,
    error: error,
  });

  return {
    error: context,
    message: errorMessage,
    timestamp,
  };
}

// Rate limiting helper (simple in-memory implementation)
const rateLimitMap = new Map<
  string,
  { count: number; resetTime: number }
>();

function rateLimit(
  identifier: string,
  maxRequests = 100,
  windowMs = 60000,
) {
  const now = Date.now();
  const record = rateLimitMap.get(identifier);

  if (!record || now > record.resetTime) {
    rateLimitMap.set(identifier, {
      count: 1,
      resetTime: now + windowMs,
    });
    return false;
  }

  if (record.count >= maxRequests) {
    return true;
  }

  record.count++;
  return false;
}

// User Registration
app.post("/make-server-3c640fc2/signup", async (c) => {
  try {
    const clientIP =
      c.req.header("cf-connecting-ip") ||
      c.req.header("x-forwarded-for") ||
      "unknown";

    if (rateLimit(clientIP, 5, 300000)) {
      // 5 signups per 5 minutes
      return c.json(
        {
          error:
            "Too many signup attempts. Please try again later.",
        },
        429,
      );
    }

    const { email, password, name } = await c.req.json();

    // Input validation
    if (!email || !password || !name) {
      return c.json(
        { error: "Email, password, and name are required" },
        400,
      );
    }

    if (password.length < 6) {
      return c.json(
        {
          error: "Password must be at least 6 characters long",
        },
        400,
      );
    }

    const { data, error } =
      await supabase.auth.admin.createUser({
        email,
        password,
        user_metadata: { name },
        // Automatically confirm the user's email since an email server hasn't been configured.
        email_confirm: true,
      });

    if (error) {
      console.log("Signup error:", error);
      return c.json({ error: error.message }, 400);
    }

    // Store additional user profile data
    await kv.set(`user:${data.user.id}:profile`, {
      id: data.user.id,
      name,
      email,
      createdAt: new Date().toISOString(),
      properties: [],
      totalRevenue: 0,
      settings: {
        notifications: {
          bookings: true,
          marketing: false,
          systemUpdates: true,
        },
        preferences: {
          currency: "USD",
          timezone: "America/New_York",
          language: "English",
        },
      },
    });

    return c.json({ user: data.user });
  } catch (error) {
    const errorDetails = handleError(
      error,
      "Signup process error",
    );
    return c.json(errorDetails, 500);
  }
});

// Get User Profile
app.get("/make-server-3c640fc2/user/profile", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    let profile = await kv.get(`user:${user.id}:profile`);

    // If profile doesn't exist (e.g., Google OAuth user), create one
    if (!profile) {
      const displayName =
        user.user_metadata?.full_name ||
        user.user_metadata?.name ||
        user.email?.split("@")[0] ||
        "User";

      profile = {
        id: user.id,
        name: displayName,
        email: user.email,
        createdAt: new Date().toISOString(),
        properties: [],
        totalRevenue: 0,
        settings: {
          notifications: {
            bookings: true,
            marketing: false,
            systemUpdates: true,
          },
          preferences: {
            currency: "USD",
            timezone: "America/New_York",
            language: "English",
          },
        },
      };

      // Save the new profile
      await kv.set(`user:${user.id}:profile`, profile);
    }

    return c.json({ profile });
  } catch (error) {
    const errorDetails = handleError(
      error,
      "Get profile error",
    );
    return c.json(errorDetails, 500);
  }
});

// Create Property
app.post("/make-server-3c640fc2/properties", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const propertyData = await c.req.json();

    // Validate property data
    const validationErrors = validatePropertyData(propertyData);
    if (validationErrors.length > 0) {
      return c.json(
        { error: validationErrors.join(", ") },
        400,
      );
    }

    const propertyId = crypto.randomUUID();

    const property = {
      id: propertyId,
      userId: user.id,
      ...propertyData,
      status: "active",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      bookings: 0,
      revenue: 0,
      rating: 0,
      reviews: 0,
    };

    await kv.set(`property:${propertyId}`, property);

    // Update user's property list
    const profile = await kv.get(`user:${user.id}:profile`);
    if (profile) {
      profile.properties.push(propertyId);
      await kv.set(`user:${user.id}:profile`, profile);
    }

    return c.json({ property });
  } catch (error) {
    console.log("Create property error:", error);
    return c.json({ error: "Failed to create property" }, 500);
  }
});

// Get User Properties
app.get("/make-server-3c640fc2/properties", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const profile = await kv.get(`user:${user.id}:profile`);
    if (!profile || !profile.properties) {
      return c.json({ properties: [] });
    }

    const properties = await kv.mget(
      profile.properties.map((id) => `property:${id}`),
    );
    return c.json({
      properties: properties.filter((p) => p !== null),
    });
  } catch (error) {
    console.log("Get properties error:", error);
    return c.json({ error: "Failed to fetch properties" }, 500);
  }
});

// Update Property
app.put("/make-server-3c640fc2/properties/:id", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const propertyId = c.req.param("id");
    const updates = await c.req.json();

    const existingProperty = await kv.get(
      `property:${propertyId}`,
    );
    if (
      !existingProperty ||
      existingProperty.userId !== user.id
    ) {
      return c.json(
        { error: "Property not found or unauthorized" },
        404,
      );
    }

    const updatedProperty = {
      ...existingProperty,
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    await kv.set(`property:${propertyId}`, updatedProperty);
    return c.json({ property: updatedProperty });
  } catch (error) {
    console.log("Update property error:", error);
    return c.json({ error: "Failed to update property" }, 500);
  }
});

// Create Booking
app.post("/make-server-3c640fc2/bookings", async (c) => {
  try {
    const bookingData = await c.req.json();
    const bookingId = "BK" + Date.now().toString();

    const booking = {
      id: bookingId,
      ...bookingData,
      status: "pending",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    await kv.set(`booking:${bookingId}`, booking);

    // Update property booking count
    const property = await kv.get(
      `property:${bookingData.propertyId}`,
    );
    if (property) {
      property.bookings = (property.bookings || 0) + 1;
      await kv.set(
        `property:${bookingData.propertyId}`,
        property,
      );
    }

    return c.json({ booking });
  } catch (error) {
    console.log("Create booking error:", error);
    return c.json({ error: "Failed to create booking" }, 500);
  }
});

// Get User Bookings
app.get("/make-server-3c640fc2/bookings", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    // Get all bookings and filter by user's properties
    const allBookings = await kv.getByPrefix("booking:");
    const userProperties = await kv.get(
      `user:${user.id}:profile`,
    );

    if (!userProperties?.properties) {
      return c.json({ bookings: [] });
    }

    const userBookings = allBookings.filter((booking) =>
      userProperties.properties.includes(booking.propertyId),
    );

    return c.json({ bookings: userBookings });
  } catch (error) {
    console.log("Get bookings error:", error);
    return c.json({ error: "Failed to fetch bookings" }, 500);
  }
});

// Update Booking Status
app.put("/make-server-3c640fc2/bookings/:id", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const bookingId = c.req.param("id");
    const updates = await c.req.json();

    const existingBooking = await kv.get(
      `booking:${bookingId}`,
    );
    if (!existingBooking) {
      return c.json({ error: "Booking not found" }, 404);
    }

    // Verify user owns the property
    const property = await kv.get(
      `property:${existingBooking.propertyId}`,
    );
    if (!property || property.userId !== user.id) {
      return c.json({ error: "Unauthorized" }, 403);
    }

    const updatedBooking = {
      ...existingBooking,
      ...updates,
      updatedAt: new Date().toISOString(),
    };

    await kv.set(`booking:${bookingId}`, updatedBooking);

    // Update property revenue if booking is confirmed
    if (
      updates.status === "confirmed" &&
      existingBooking.status !== "confirmed"
    ) {
      property.revenue =
        (property.revenue || 0) + existingBooking.amount;
      await kv.set(
        `property:${existingBooking.propertyId}`,
        property,
      );
    }

    return c.json({ booking: updatedBooking });
  } catch (error) {
    console.log("Update booking error:", error);
    return c.json({ error: "Failed to update booking" }, 500);
  }
});

// Get Analytics Data
app.get("/make-server-3c640fc2/analytics", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const profile = await kv.get(`user:${user.id}:profile`);
    if (!profile?.properties) {
      return c.json({
        totalRevenue: 0,
        totalBookings: 0,
        totalProperties: 0,
        occupancyRate: 0,
        monthlyData: [],
        propertyPerformance: [],
        marketInsights: {
          marketHealthScore: 0,
          competitivePosition: 0,
          seasonalTrends: {},
          demandPatterns: [],
        },
        forecast: {
          nextQuarterRevenue: 0,
          confidence: 0,
          peakPeriod: null,
        },
        recommendations: [],
      });
    }

    // Get user's properties
    const properties = await kv.mget(
      profile.properties.map((id) => `property:${id}`),
    );
    const validProperties = properties.filter(
      (p) => p !== null,
    );

    // Get all bookings for user's properties
    const allBookings = await kv.getByPrefix("booking:");
    const userBookings = allBookings.filter(
      (booking) =>
        profile.properties.includes(booking.propertyId) &&
        booking.status === "confirmed",
    );

    const totalRevenue = userBookings.reduce(
      (sum, booking) => sum + booking.amount,
      0,
    );
    const totalBookings = userBookings.length;
    const totalProperties = validProperties.length;

    // Calculate occupancy rate (simplified)
    const occupancyRate =
      totalBookings > 0
        ? Math.min(85, 40 + totalBookings * 2)
        : 0;

    // Generate monthly data for the last 12 months
    const monthlyData = [];
    const now = new Date();
    for (let i = 11; i >= 0; i--) {
      const month = new Date(
        now.getFullYear(),
        now.getMonth() - i,
        1,
      );
      const monthStr = month.toISOString().substring(0, 7);

      const monthBookings = userBookings.filter((booking) =>
        booking.createdAt.startsWith(monthStr),
      );

      monthlyData.push({
        month: month.toLocaleDateString("en-US", {
          month: "short",
        }),
        revenue: monthBookings.reduce(
          (sum, booking) => sum + booking.amount,
          0,
        ),
        bookings: monthBookings.length,
      });
    }

    // Property performance with enhanced metrics
    const propertyPerformance = validProperties.map(
      (property) => {
        const propertyBookings = userBookings.filter(
          (b) => b.propertyId === property.id,
        );
        const revenue = propertyBookings.reduce(
          (sum, booking) => sum + booking.amount,
          0,
        );
        const avgDailyRate =
          propertyBookings.length > 0
            ? revenue / propertyBookings.length
            : 0;
        const revPAR = revenue / 365; // Revenue per available room per year (simplified)

        return {
          name: property.title,
          revenue: revenue,
          bookings: propertyBookings.length,
          rating: property.rating || 4.5 + Math.random() * 0.4,
          occupancyRate: Math.min(
            95,
            property.bookings * 3 + Math.random() * 10,
          ),
          avgDailyRate: Math.round(avgDailyRate),
          revPAR: Math.round(revPAR),
        };
      },
    );

    // Market insights and competitive analysis
    const marketInsights = {
      marketHealthScore: Math.floor(75 + Math.random() * 20), // Simulated market health
      competitivePosition: Math.floor(Math.random() * 5) + 1, // Ranking out of nearby properties
      seasonalTrends: {
        spring: "High",
        summer: "Peak",
        fall: "Medium",
        winter: "Low",
      },
      demandPatterns: [
        { hour: "00", weekday: 2, weekend: 5 },
        { hour: "06", weekday: 8, weekend: 12 },
        { hour: "12", weekday: 25, weekend: 35 },
        { hour: "18", weekday: 45, weekend: 65 },
        { hour: "21", weekday: 35, weekend: 55 },
      ],
    };

    // Revenue forecasting (simplified AI simulation)
    const avgMonthlyRevenue = totalRevenue / 12;
    const growthTrend = 1.15; // 15% growth assumption
    const nextQuarterRevenue = Math.round(
      avgMonthlyRevenue * 3 * growthTrend,
    );

    const forecast = {
      nextQuarterRevenue: nextQuarterRevenue,
      confidence: Math.floor(80 + Math.random() * 15), // 80-95% confidence
      peakPeriod: "July 2024",
      monthlyForecast: [
        {
          month: "Jul",
          forecast: Math.round(avgMonthlyRevenue * 1.4),
          confidence: 89,
        },
        {
          month: "Aug",
          forecast: Math.round(avgMonthlyRevenue * 1.3),
          confidence: 86,
        },
        {
          month: "Sep",
          forecast: Math.round(avgMonthlyRevenue * 1.1),
          confidence: 83,
        },
      ],
    };

    // AI-powered recommendations
    const recommendations = [
      {
        type: "pricing",
        title: "Optimize Weekend Pricing",
        description:
          "Increase weekend rates by 15-20% based on demand patterns",
        impact: "High",
        effort: "Low",
        potentialRevenue: Math.round(totalRevenue * 0.15),
      },
      {
        type: "occupancy",
        title: "Midweek Promotions",
        description:
          "Offer weekday discounts to improve occupancy during low-demand periods",
        impact: "Medium",
        effort: "Medium",
        potentialRevenue: Math.round(totalRevenue * 0.08),
      },
      {
        type: "market",
        title: "Seasonal Strategy",
        description:
          "Adjust pricing strategy for upcoming peak summer season",
        impact: "High",
        effort: "Medium",
        potentialRevenue: Math.round(totalRevenue * 0.22),
      },
    ];

    // Competitive benchmarking
    const marketComparison = {
      avgDailyRate: {
        myProperty:
          Math.round(totalRevenue / totalBookings) || 120,
        marketAverage: 115,
        percentile: 68,
      },
      occupancyRate: {
        myProperty: occupancyRate,
        marketAverage: occupancyRate - 4,
        percentile: 72,
      },
      revPAR: {
        myProperty: Math.round(
          (totalRevenue / totalBookings || 120) *
            (occupancyRate / 100),
        ),
        marketAverage: 95,
        percentile: 78,
      },
    };

    return c.json({
      totalRevenue,
      totalBookings,
      totalProperties,
      occupancyRate,
      monthlyData,
      propertyPerformance,
      marketInsights,
      forecast,
      recommendations,
      marketComparison,
      pricingOptimization: {
        currentRevenue: totalRevenue,
        optimizedRevenue: Math.round(totalRevenue * 1.18),
        potentialLift: 18,
        confidence: 87,
      },
    });
  } catch (error) {
    console.log("Get analytics error:", error);
    return c.json({ error: "Failed to fetch analytics" }, 500);
  }
});

// New endpoint for market data
app.get("/make-server-3c640fc2/analytics/market", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    // Simulated market data for demo purposes
    const marketData = {
      competitors: [
        {
          name: "Luxury Downtown Loft",
          distance: 0.3,
          rate: 165,
          rating: 4.9,
          occupancy: 85,
        },
        {
          name: "Modern City Apartment",
          distance: 0.5,
          rate: 125,
          rating: 4.7,
          occupancy: 78,
        },
        {
          name: "Executive Suite",
          distance: 0.8,
          rate: 195,
          rating: 4.8,
          occupancy: 72,
        },
        {
          name: "Urban Retreat",
          distance: 1.2,
          rate: 110,
          rating: 4.6,
          occupancy: 68,
        },
      ],
      marketTrends: {
        demandGrowth: 23,
        priceGrowth: 8.5,
        newSupply: 12,
        seasonality: {
          peak: {
            months: ["Jun", "Jul", "Aug"],
            multiplier: 1.4,
          },
          low: {
            months: ["Jan", "Feb", "Mar"],
            multiplier: 0.7,
          },
        },
      },
      localEvents: [
        {
          name: "Tech Conference",
          date: "2024-07-15",
          impact: "High",
          duration: 3,
        },
        {
          name: "Music Festival",
          date: "2024-08-20",
          impact: "Very High",
          duration: 5,
        },
        {
          name: "Trade Show",
          date: "2024-09-10",
          impact: "Medium",
          duration: 2,
        },
      ],
    };

    return c.json(marketData);
  } catch (error) {
    console.log("Get market data error:", error);
    return c.json(
      { error: "Failed to fetch market data" },
      500,
    );
  }
});

// New endpoint for pricing optimization
app.post(
  "/make-server-3c640fc2/analytics/pricing-optimization",
  async (c) => {
    try {
      const accessToken = c.req
        .header("Authorization")
        ?.split(" ")[1];
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser(accessToken);

      if (!user?.id) {
        return c.json({ error: "Unauthorized" }, 401);
      }

      const { dateRange, propertyId } = await c.req.json();

      // Simulated pricing optimization algorithm
      const optimizedPricing = [
        {
          date: "Mon 15",
          current: 120,
          suggested: 135,
          demand: "High",
          events: ["Conference"],
        },
        {
          date: "Tue 16",
          current: 120,
          suggested: 110,
          demand: "Low",
          events: [],
        },
        {
          date: "Wed 17",
          current: 120,
          suggested: 145,
          demand: "Very High",
          events: ["Concert", "Trade Show"],
        },
        {
          date: "Thu 18",
          current: 120,
          suggested: 125,
          demand: "Medium",
          events: [],
        },
        {
          date: "Fri 19",
          current: 150,
          suggested: 165,
          demand: "High",
          events: ["Weekend"],
        },
        {
          date: "Sat 20",
          current: 180,
          suggested: 195,
          demand: "Very High",
          events: ["Weekend", "Festival"],
        },
        {
          date: "Sun 21",
          current: 160,
          suggested: 145,
          demand: "Medium",
          events: ["Weekend"],
        },
      ];

      const totalCurrentRevenue = optimizedPricing.reduce(
        (sum, day) => sum + day.current,
        0,
      );
      const totalOptimizedRevenue = optimizedPricing.reduce(
        (sum, day) => sum + day.suggested,
        0,
      );
      const potentialLift = (
        ((totalOptimizedRevenue - totalCurrentRevenue) /
          totalCurrentRevenue) *
        100
      ).toFixed(1);

      return c.json({
        optimizedPricing,
        summary: {
          currentRevenue: totalCurrentRevenue,
          optimizedRevenue: totalOptimizedRevenue,
          potentialLift: parseFloat(potentialLift),
          confidence: 89,
        },
      });
    } catch (error) {
      console.log("Pricing optimization error:", error);
      return c.json(
        { error: "Failed to generate pricing optimization" },
        500,
      );
    }
  },
);

// Health check
app.get("/make-server-3c640fc2/health", (c) => {
  return c.json({
    status: "OK",
    timestamp: new Date().toISOString(),
  });
});

// Debug endpoint to check demo user
app.get("/make-server-3c640fc2/debug/demo-user", async (c) => {
  try {
    // Check if demo user exists in Supabase Auth
    const { data: existingUsers } =
      await supabase.auth.admin.listUsers();
    const demoUser = existingUsers?.users?.find(
      (user) => user.email === "demo@rentalai.com",
    );

    let demoProfile = null;
    if (demoUser) {
      demoProfile = await kv.get(`user:${demoUser.id}:profile`);
    }

    return c.json({
      demoUserExists: !!demoUser,
      demoUserId: demoUser?.id,
      demoUserConfirmed: demoUser?.email_confirmed_at !== null,
      profileExists: !!demoProfile,
      profileData: demoProfile
        ? {
            id: demoProfile.id,
            name: demoProfile.name,
            email: demoProfile.email,
            propertiesCount:
              demoProfile.properties?.length || 0,
          }
        : null,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.log("Debug demo user error:", error);
    return c.json(
      {
        error: "Failed to check demo user",
        details: error.message,
      },
      500,
    );
  }
});

// Upload Property Image
app.post(
  "/make-server-3c640fc2/properties/:id/images",
  async (c) => {
    try {
      const accessToken = c.req
        .header("Authorization")
        ?.split(" ")[1];
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser(accessToken);

      if (!user?.id) {
        return c.json({ error: "Unauthorized" }, 401);
      }

      const propertyId = c.req.param("id");

      // Verify user owns the property
      const property = await kv.get(`property:${propertyId}`);
      if (!property || property.userId !== user.id) {
        return c.json(
          { error: "Property not found or unauthorized" },
          404,
        );
      }

      const formData = await c.req.formData();
      const file = formData.get("image") as File;

      if (!file) {
        return c.json({ error: "No image file provided" }, 400);
      }

      const result = await uploadPropertyImage(
        user.id,
        propertyId,
        file,
      );

      if (result.error) {
        return c.json({ error: result.error }, 400);
      }

      // Update property with new image URL
      const updatedProperty = {
        ...property,
        images: [...(property.images || []), result.url],
        updatedAt: new Date().toISOString(),
      };

      await kv.set(`property:${propertyId}`, updatedProperty);

      return c.json({
        message: "Image uploaded successfully",
        imageUrl: result.url,
        property: updatedProperty,
      });
    } catch (error) {
      const errorDetails = handleError(
        error,
        "Image upload error",
      );
      return c.json(errorDetails, 500);
    }
  },
);

// Get Property Images
app.get(
  "/make-server-3c640fc2/properties/:id/images",
  async (c) => {
    try {
      const accessToken = c.req
        .header("Authorization")
        ?.split(" ")[1];
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser(accessToken);

      if (!user?.id) {
        return c.json({ error: "Unauthorized" }, 401);
      }

      const propertyId = c.req.param("id");

      const result = await getPropertyImages(
        propertyId,
        user.id,
      );

      if (result.error) {
        return c.json({ error: result.error }, 400);
      }

      return c.json({ images: result.images });
    } catch (error) {
      const errorDetails = handleError(
        error,
        "Get images error",
      );
      return c.json(errorDetails, 500);
    }
  },
);

// Update User Settings
app.put("/make-server-3c640fc2/user/settings", async (c) => {
  try {
    const accessToken = c.req
      .header("Authorization")
      ?.split(" ")[1];
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(accessToken);

    if (!user?.id) {
      return c.json({ error: "Unauthorized" }, 401);
    }

    const settings = await c.req.json();

    const profile = await kv.get(`user:${user.id}:profile`);
    if (!profile) {
      return c.json({ error: "Profile not found" }, 404);
    }

    const updatedProfile = {
      ...profile,
      settings: { ...profile.settings, ...settings },
      updatedAt: new Date().toISOString(),
    };

    await kv.set(`user:${user.id}:profile`, updatedProfile);

    return c.json({
      message: "Settings updated successfully",
      profile: updatedProfile,
    });
  } catch (error) {
    const errorDetails = handleError(
      error,
      "Update settings error",
    );
    return c.json(errorDetails, 500);
  }
});

// Enhanced Property Validation
function validatePropertyData(propertyData: any) {
  const errors: string[] = [];

  if (
    !propertyData.title ||
    propertyData.title.trim().length < 3
  ) {
    errors.push("Title must be at least 3 characters long");
  }

  if (
    !propertyData.description ||
    propertyData.description.trim().length < 10
  ) {
    errors.push(
      "Description must be at least 10 characters long",
    );
  }

  if (
    !propertyData.address ||
    propertyData.address.trim().length < 5
  ) {
    errors.push("Address must be at least 5 characters long");
  }

  if (
    !propertyData.pricePerNight ||
    propertyData.pricePerNight < 1
  ) {
    errors.push("Price per night must be at least $1");
  }

  if (!propertyData.bedrooms || propertyData.bedrooms < 0) {
    errors.push("Number of bedrooms must be 0 or greater");
  }

  if (!propertyData.bathrooms || propertyData.bathrooms < 0.5) {
    errors.push("Number of bathrooms must be 0.5 or greater");
  }

  if (!propertyData.maxGuests || propertyData.maxGuests < 1) {
    errors.push("Maximum guests must be at least 1");
  }

  if (
    !propertyData.propertyType ||
    ![
      "apartment",
      "house",
      "condo",
      "villa",
      "studio",
      "other",
    ].includes(propertyData.propertyType)
  ) {
    errors.push("Invalid property type");
  }

  return errors;
}

Deno.serve(app.fetch);