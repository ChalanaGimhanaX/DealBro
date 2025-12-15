import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'DealBro - Hosting Deals Aggregator',
  description: 'Find the best hosting deals from multiple sources',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 min-h-screen`}>
        <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
                  <span className="text-white font-bold text-lg">D</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">DealBro</h1>
                  <p className="text-xs text-gray-500">Hosting Deals Aggregator</p>
                </div>
              </div>
              <nav className="hidden sm:flex items-center space-x-6">
                <a href="/" className="text-sm font-medium text-gray-700 hover:text-primary-600 transition">Deals</a>
                <a href="#" className="text-sm font-medium text-gray-500 hover:text-primary-600 transition">VPS</a>
                <a href="#" className="text-sm font-medium text-gray-500 hover:text-primary-600 transition">Dedicated</a>
              </nav>
            </div>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="bg-white border-t border-gray-200 mt-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <p className="text-center text-sm text-gray-500">
              &copy; 2025 DealBro. Aggregating hosting deals from LowEndTalk, LowEndBox, WebHostingTalk & more.
            </p>
          </div>
        </footer>
      </body>
    </html>
  )
}
