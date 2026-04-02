"use client";

import { createAuthClient } from "better-auth/react";

export const authClient = createAuthClient({
  baseURL: typeof window !== 'undefined'
    ? (process.env.NEXT_PUBLIC_APP_URL || window.location.origin)
    : "http://localhost:3000",
});

export const {
  signIn,
  signUp,
  signOut,
  useSession,
  getSession,
} = authClient;

// Password reset & account management — accessed via $fetch to avoid TS inference issues
// Better Auth exposes these when emailAndPassword is enabled on the server
export const forgetPassword = async ({ email, redirectTo }: { email: string; redirectTo: string }) => {
  return authClient.$fetch('/forget-password', {
    method: 'POST',
    body: { email, redirectTo },
  });
};

export const resetPassword = async ({ newPassword }: { newPassword: string }) => {
  // Better Auth reads the token from the URL callback
  const token = typeof window !== 'undefined'
    ? new URLSearchParams(window.location.search).get('token')
    : null;
  return authClient.$fetch('/reset-password', {
    method: 'POST',
    body: { newPassword, token },
  });
};

export const changePassword = async ({ currentPassword, newPassword }: { currentPassword: string; newPassword: string }) => {
  return authClient.$fetch('/change-password', {
    method: 'POST',
    body: { currentPassword, newPassword },
  });
};

export const updateUser = async ({ name }: { name: string }) => {
  return authClient.$fetch('/update-user', {
    method: 'POST',
    body: { name },
  });
};
