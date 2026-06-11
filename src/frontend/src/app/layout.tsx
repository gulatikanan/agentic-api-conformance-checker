import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'API Conformance Dashboard',
  description: 'Enterprise Automated Compliance Auditing Workspace',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="bg-slate-950 text-slate-100">
      <body>{children}</body>
    </html>
  )
}
