"use client";

import { useState, useRef, useEffect } from 'react';
import { Link, useRouter, usePathname } from '@/i18n/navigation';
import { useTranslations, useLocale } from 'next-intl';
import { useAuth } from '@/contexts/AuthContext';
import { LogOut, Globe, Settings, ChevronDown } from 'lucide-react';
import AppArtLogo from './AppArtLogo';

export default function Header() {
  const { user, logout, isAuthenticated, loading } = useAuth();
  const t = useTranslations('header');
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

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

            {!loading && isAuthenticated && (
              <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
                <Link
                  href="/dashboard"
                  className="border-transparent text-gray-500 hover:border-primary-500 hover:text-primary-600 inline-flex items-center justify-center min-w-[9rem] px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                >
                  {t('dashboard')}
                </Link>
                <Link
                  href="/properties"
                  className="border-transparent text-gray-500 hover:border-primary-500 hover:text-primary-600 inline-flex items-center justify-center min-w-[5.5rem] px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
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

            {loading ? (
              <div className="flex items-center">
                <div className="h-5 w-24 bg-gray-200 rounded animate-pulse" />
              </div>
            ) : isAuthenticated ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
                >
                  <span>{user?.full_name}</span>
                  <ChevronDown className={`h-4 w-4 text-gray-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                    <Link
                      href="/settings"
                      onClick={() => setDropdownOpen(false)}
                      className="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      <Settings className="h-4 w-4 text-gray-400" />
                      {t('settings')}
                    </Link>
                    <hr className="my-1 border-gray-100" />
                    <button
                      onClick={() => { setDropdownOpen(false); logout(); }}
                      className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
                    >
                      <LogOut className="h-4 w-4 text-gray-400" />
                      {t('logout')}
                    </button>
                  </div>
                )}
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
