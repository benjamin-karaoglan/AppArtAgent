"use client";

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useTranslations, useLocale } from 'next-intl';
import { useRouter, usePathname } from '@/i18n/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { changePassword, updateUser } from '@/lib/auth-client';
import { api } from '@/lib/api';
import Header from '@/components/Header';
import ProtectedRoute from '@/components/ProtectedRoute';
import { User, Lock, Globe, AlertTriangle, Check } from 'lucide-react';

// --- Profile Section ---
function ProfileSection() {
  const t = useTranslations('settings.profile');
  const { user, refreshSession } = useAuth();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { name: user?.full_name || '' },
  });

  const onSubmit = async (data: { name: string }) => {
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      await updateUser({ name: data.name });
      if (refreshSession) await refreshSession();
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch {
      setError(t('errors.failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <User className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">{t('title')}</h2>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
            {t('name')}
          </label>
          <input
            id="name"
            type="text"
            {...register('name', { required: t('errors.nameRequired') })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            placeholder={t('namePlaceholder')}
          />
          {errors.name && <p className="mt-1 text-sm text-danger-600">{errors.name.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t('email')}</label>
          <input
            type="email"
            value={user?.email || ''}
            disabled
            className="block w-full px-3 py-2 border border-gray-200 rounded-md text-gray-500 bg-gray-50 sm:text-sm cursor-not-allowed"
          />
          <p className="mt-1 text-xs text-gray-400">{t('emailReadOnly')}</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? t('saving') : t('save')}
          </button>
          {success && (
            <span className="flex items-center gap-1 text-sm text-success-600">
              <Check className="w-4 h-4" /> {t('saved')}
            </span>
          )}
          {error && <span className="text-sm text-danger-600">{error}</span>}
        </div>
      </form>
    </section>
  );
}

// --- Password Section ---
function PasswordSection() {
  const t = useTranslations('settings.password');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm({
    defaultValues: { currentPassword: '', newPassword: '', confirmPassword: '' },
  });

  const onSubmit = async (data: { currentPassword: string; newPassword: string }) => {
    setError('');
    setSuccess(false);
    setLoading(true);

    try {
      const result = await changePassword({
        currentPassword: data.currentPassword,
        newPassword: data.newPassword,
      });

      if (result.error) {
        if (result.error.message?.toLowerCase().includes('incorrect') ||
            result.error.message?.toLowerCase().includes('invalid')) {
          setError(t('errors.wrongCurrent'));
        } else {
          setError(result.error.message || t('errors.failed'));
        }
      } else {
        setSuccess(true);
        reset();
        setTimeout(() => setSuccess(false), 3000);
      }
    } catch {
      setError(t('errors.failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <Lock className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">{t('title')}</h2>
      </div>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="currentPassword" className="block text-sm font-medium text-gray-700 mb-1">
            {t('current')}
          </label>
          <input
            id="currentPassword"
            type="password"
            autoComplete="current-password"
            {...register('currentPassword', { required: t('errors.currentRequired') })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            placeholder={t('currentPlaceholder')}
          />
          {errors.currentPassword && (
            <p className="mt-1 text-sm text-danger-600">{errors.currentPassword.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700 mb-1">
            {t('new')}
          </label>
          <input
            id="newPassword"
            type="password"
            autoComplete="new-password"
            {...register('newPassword', {
              required: t('errors.newRequired'),
              minLength: { value: 8, message: t('errors.newMinLength', { min: 8 }) },
            })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            placeholder={t('newPlaceholder')}
          />
          {errors.newPassword && (
            <p className="mt-1 text-sm text-danger-600">{errors.newPassword.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-1">
            {t('confirm')}
          </label>
          <input
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            {...register('confirmPassword', {
              required: t('errors.confirmRequired'),
              validate: (val) => val === watch('newPassword') || t('errors.mismatch'),
            })}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            placeholder={t('confirmPlaceholder')}
          />
          {errors.confirmPassword && (
            <p className="mt-1 text-sm text-danger-600">{errors.confirmPassword.message}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? t('submitting') : t('submit')}
          </button>
          {success && (
            <span className="flex items-center gap-1 text-sm text-success-600">
              <Check className="w-4 h-4" /> {t('changed')}
            </span>
          )}
          {error && <span className="text-sm text-danger-600">{error}</span>}
        </div>
      </form>
    </section>
  );
}

// --- Language Section ---
function LanguageSection() {
  const t = useTranslations('settings.language');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (newLocale: string) => {
    router.replace(pathname, { locale: newLocale as 'fr' | 'en' });
  };

  return (
    <section className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-2 mb-4">
        <Globe className="w-5 h-5 text-gray-600" />
        <h2 className="text-lg font-semibold text-gray-900">{t('title')}</h2>
      </div>
      <p className="text-sm text-gray-600 mb-4">{t('description')}</p>
      <div className="flex gap-3">
        <button
          onClick={() => switchLocale('fr')}
          className={`px-4 py-2 text-sm font-medium rounded-md border transition-colors ${
            locale === 'fr'
              ? 'bg-primary-50 border-primary-300 text-primary-700'
              : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          {t('french')}
        </button>
        <button
          onClick={() => switchLocale('en')}
          className={`px-4 py-2 text-sm font-medium rounded-md border transition-colors ${
            locale === 'en'
              ? 'bg-primary-50 border-primary-300 text-primary-700'
              : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
          }`}
        >
          {t('english')}
        </button>
      </div>
    </section>
  );
}

// --- Danger Zone Section ---
function DangerZoneSection() {
  const t = useTranslations('settings.dangerZone');
  const tc = useTranslations('common');
  const locale = useLocale();
  const { logout } = useAuth();
  const [showModal, setShowModal] = useState(false);
  const [confirmText, setConfirmText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const confirmWord = locale === 'fr' ? 'SUPPRIMER' : 'DELETE';

  const handleDelete = async () => {
    if (confirmText !== confirmWord) {
      setError(t('errors.confirmMismatch'));
      return;
    }

    setError('');
    setLoading(true);

    try {
      await api.delete('/api/users/me');
      await logout();
    } catch {
      setError(t('errors.failed'));
      setLoading(false);
    }
  };

  return (
    <>
      <section className="bg-white rounded-lg shadow p-6 border border-danger-200">
        <div className="flex items-center gap-2 mb-4">
          <AlertTriangle className="w-5 h-5 text-danger-600" />
          <h2 className="text-lg font-semibold text-danger-900">{t('title')}</h2>
        </div>
        <p className="text-sm text-gray-600 mb-4">{t('deleteDescription')}</p>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 text-sm font-medium text-white bg-danger-600 rounded-md hover:bg-danger-700"
        >
          {t('deleteButton')}
        </button>
      </section>

      {/* Delete confirmation modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-6 h-6 text-danger-600" />
              <h3 className="text-lg font-semibold text-gray-900">{t('confirmTitle')}</h3>
            </div>
            <p className="text-sm text-gray-600">{t('confirmMessage')}</p>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('confirmInstruction')}
              </label>
              <input
                type="text"
                value={confirmText}
                onChange={(e) => setConfirmText(e.target.value)}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 bg-white focus:outline-none focus:ring-danger-500 focus:border-danger-500 sm:text-sm"
                placeholder={t('confirmPlaceholder')}
                autoFocus
              />
            </div>
            {error && <p className="text-sm text-danger-600">{error}</p>}
            <div className="flex justify-end gap-3">
              <button
                onClick={() => { setShowModal(false); setConfirmText(''); setError(''); }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={loading}
              >
                {tc('cancel')}
              </button>
              <button
                onClick={handleDelete}
                disabled={loading || confirmText !== confirmWord}
                className="px-4 py-2 text-sm font-medium text-white bg-danger-600 rounded-md hover:bg-danger-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? t('deleting') : t('confirmButton')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// --- Main Settings Page ---
export default function SettingsPage() {
  const t = useTranslations('settings');

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <Header />
        <div className="container mx-auto px-4 py-8 max-w-2xl">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('title')}</h1>
          <div className="space-y-6">
            <ProfileSection />
            <PasswordSection />
            <LanguageSection />
            <DangerZoneSection />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
