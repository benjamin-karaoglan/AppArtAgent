"use client";

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from '@/i18n/navigation';
import { useTranslations } from 'next-intl';
import { resetPassword } from '@/lib/auth-client';
import { Lock, CheckCircle } from 'lucide-react';
import Header from '@/components/Header';

interface ResetPasswordForm {
  password: string;
  confirmPassword: string;
}

export default function ResetPasswordPage() {
  const t = useTranslations('auth.resetPassword');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ResetPasswordForm>();

  const onSubmit = async (data: ResetPasswordForm) => {
    setError('');
    setLoading(true);

    try {
      const result = await resetPassword({
        newPassword: data.password,
      });

      if (result.error) {
        setError(result.error.message || t('errors.failed'));
      } else {
        setSuccess(true);
      }
    } catch {
      setError(t('errors.failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          {success ? (
            <div className="text-center space-y-4">
              <CheckCircle className="w-16 h-16 text-success-500 mx-auto" />
              <h2 className="text-2xl font-bold text-gray-900">{t('successTitle')}</h2>
              <p className="text-gray-600">{t('successMessage')}</p>
              <Link
                href="/auth/login"
                className="inline-flex items-center justify-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                {t('goToLogin')}
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center">
                <Lock className="w-12 h-12 text-primary-600 mx-auto mb-4" />
                <h2 className="text-3xl font-extrabold text-gray-900">{t('title')}</h2>
                <p className="mt-2 text-sm text-gray-600">{t('subtitle')}</p>
              </div>

              <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
                {error && (
                  <div className="rounded-md bg-danger-50 p-4">
                    <p className="text-sm text-danger-700">{error}</p>
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                      {t('newPassword')}
                    </label>
                    <input
                      id="password"
                      type="password"
                      autoComplete="new-password"
                      {...register('password', {
                        required: t('errors.passwordRequired'),
                        minLength: {
                          value: 8,
                          message: t('errors.passwordMinLength', { min: 8 }),
                        },
                      })}
                      className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-500 text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      placeholder={t('newPasswordPlaceholder')}
                    />
                    {errors.password && (
                      <p className="mt-1 text-sm text-danger-600">{errors.password.message}</p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
                      {t('confirmPassword')}
                    </label>
                    <input
                      id="confirmPassword"
                      type="password"
                      autoComplete="new-password"
                      {...register('confirmPassword', {
                        required: t('errors.confirmPasswordRequired'),
                        validate: (val) =>
                          val === watch('password') || t('errors.passwordsMismatch'),
                      })}
                      className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-500 text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                      placeholder={t('confirmPasswordPlaceholder')}
                    />
                    {errors.confirmPassword && (
                      <p className="mt-1 text-sm text-danger-600">{errors.confirmPassword.message}</p>
                    )}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? t('submitting') : t('submit')}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
