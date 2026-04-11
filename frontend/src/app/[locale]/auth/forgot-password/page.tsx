"use client";

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from '@/i18n/navigation';
import { useTranslations } from 'next-intl';
import { forgetPassword } from '@/lib/auth-client';
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import Header from '@/components/Header';

interface ForgotPasswordForm {
  email: string;
}

export default function ForgotPasswordPage() {
  const t = useTranslations('auth.forgotPassword');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordForm>();

  const onSubmit = async (data: ForgotPasswordForm) => {
    setError('');
    setLoading(true);

    try {
      await forgetPassword({
        email: data.email,
        redirectTo: '/auth/reset-password',
      });
      setSent(true);
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
          {sent ? (
            <div className="text-center space-y-4">
              <CheckCircle className="w-16 h-16 text-success-500 mx-auto" />
              <h2 className="text-2xl font-bold text-gray-900">{t('successTitle')}</h2>
              <p className="text-gray-600">{t('successMessage')}</p>
              <Link
                href="/auth/login"
                className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-500 font-medium"
              >
                <ArrowLeft className="w-4 h-4" />
                {t('backToLogin')}
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center">
                <Mail className="w-12 h-12 text-primary-600 mx-auto mb-4" />
                <h2 className="text-3xl font-extrabold text-gray-900">{t('title')}</h2>
                <p className="mt-2 text-sm text-gray-600">{t('subtitle')}</p>
              </div>

              <form className="mt-8 space-y-6" onSubmit={handleSubmit(onSubmit)}>
                {error && (
                  <div className="rounded-md bg-danger-50 p-4">
                    <p className="text-sm text-danger-700">{error}</p>
                  </div>
                )}

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                    {t('email')}
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    {...register('email', {
                      required: t('errors.emailRequired'),
                      pattern: {
                        value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                        message: t('errors.emailInvalid'),
                      },
                    })}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-500 text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    placeholder={t('emailPlaceholder')}
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-danger-600">{errors.email.message}</p>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? t('submitting') : t('submit')}
                </button>

                <div className="text-center">
                  <Link
                    href="/auth/login"
                    className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
                  >
                    <ArrowLeft className="w-4 h-4" />
                    {t('backToLogin')}
                  </Link>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
