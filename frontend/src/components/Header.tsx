"use client";

import { Link, useRouter, usePathname } from '@/i18n/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { LogOut, User, Globe } from 'lucide-react';
import AppArtLogo from './AppArtLogo';

export default function Header() {
  const { user, logout, isAuthenticated } = useAuth();
  const t = useTranslations('header');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (newLocale: string) => {
    router.replace(pathname, { locale: newLocale as 'fr' | 'en' });
  };

  return (
    <header className="bg-white shadow">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link href="/" className="flex items-center">
              <AppArtLogo size={36} className="text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">{t('appName')}</span>
            </Link>

            {isAuthenticated && (
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                <Link
                  href="/dashboard"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center justify-center min-w-[9rem] px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  {t('dashboard')}
                </Link>
                <Link
                  href="/properties"
                  className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center justify-center min-w-[5.5rem] px-1 pt-1 border-b-2 text-sm font-medium"
                >
                  {t('properties')}
                </Link>
              </div>
            )}
          </div>

          <div className="flex items-center">
            {/* Language Switcher */}
            <button
              onClick={() => switchLocale(locale === 'fr' ? 'en' : 'fr')}
              className="inline-flex items-center px-2 py-1 mr-3 text-sm font-medium text-gray-600 hover:text-gray-900 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              title={locale === 'fr' ? 'Switch to English' : 'Passer en français'}
            >
              <Globe className="h-4 w-4 mr-1" />
              {locale === 'fr' ? 'EN' : 'FR'}
            </button>

            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                <div className="flex items-center text-sm text-gray-700">
                  <User className="h-5 w-5 mr-2 text-gray-400" />
                  <span>{user?.full_name}</span>
                </div>
                <button
                  onClick={logout}
                  className="inline-flex items-center justify-center min-w-[8.5rem] px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 transition-colors"
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  {t('logout')}
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  href="/auth/login"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 text-sm font-medium text-center min-w-[6.5rem]"
                >
                  {t('login')}
                </Link>
                <Link
                  href="/auth/register"
                  className="inline-flex items-center justify-center min-w-[7.5rem] px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  {t('getStarted')}
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>
    </header>
  );
}
