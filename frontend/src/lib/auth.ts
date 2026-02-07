import { betterAuth } from "better-auth";
import { Pool } from "pg";

// Derive cookie domain from BETTER_AUTH_URL for cross-subdomain cookie sharing
// In production: BETTER_AUTH_URL=https://appartagent.com → domain=".appartagent.com"
// This allows the session cookie to be sent to api.appartagent.com
const betterAuthUrl = process.env.BETTER_AUTH_URL;
const cookieDomain = betterAuthUrl
  ? `.${new URL(betterAuthUrl).hostname}`
  : undefined;

export const auth = betterAuth({
  database: new Pool({
    connectionString: process.env.DATABASE_URL,
  }),
  emailAndPassword: {
    enabled: true,
    minPasswordLength: 8,
  },
  socialProviders: {
    ...(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
      ? { google: { clientId: process.env.GOOGLE_CLIENT_ID, clientSecret: process.env.GOOGLE_CLIENT_SECRET } }
      : {}),
  },
  // Enable cross-subdomain cookies so session is shared between
  // appartagent.com (frontend) and api.appartagent.com (backend)
  advanced: {
    crossSubDomainCookies: {
      enabled: !!cookieDomain,
      domain: cookieDomain || "",
    },
  },
  // Trust the API subdomain for CSRF protection
  trustedOrigins: [
    ...(betterAuthUrl
      ? [`https://api.${new URL(betterAuthUrl).hostname}`]
      : []),
  ],
  session: {
    modelName: "ba_session",
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    cookieCache: {
      enabled: true,
      maxAge: 60 * 5, // 5 minutes
    },
    fields: {
      userId: "user_id",
      expiresAt: "expires_at",
      ipAddress: "ip_address",
      userAgent: "user_agent",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
  },
  user: {
    modelName: "ba_user",
    additionalFields: {
      is_active: {
        type: "boolean",
        defaultValue: true,
        input: false,
      },
      is_superuser: {
        type: "boolean",
        defaultValue: false,
        input: false,
      },
    },
    fields: {
      emailVerified: "email_verified",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
  },
  account: {
    modelName: "ba_account",
    fields: {
      userId: "user_id",
      accountId: "account_id",
      providerId: "provider_id",
      accessToken: "access_token",
      refreshToken: "refresh_token",
      idToken: "id_token",
      accessTokenExpiresAt: "access_token_expires_at",
      refreshTokenExpiresAt: "refresh_token_expires_at",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
  },
  verification: {
    modelName: "ba_verification",
    fields: {
      expiresAt: "expires_at",
      createdAt: "created_at",
      updatedAt: "updated_at",
    },
  },
  databaseHooks: {
    user: {
      create: {
        before: async (user) => {
          return {
            data: {
              ...user,
              is_active: true,
              is_superuser: false,
            },
          };
        },
      },
    },
  },
});

export type Session = typeof auth.$Infer.Session;
export type User = typeof auth.$Infer.Session.user;
