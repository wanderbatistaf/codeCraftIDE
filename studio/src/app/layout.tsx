import type {Metadata} from 'next';
import './globals.css';
import { cn } from '@/lib/utils';
import { Toaster } from '@/components/ui/toaster';
import { SessionProvider } from '@/contexts/session-context';
import { FileSystemProvider } from '@/contexts/file-system-context';
import { DatabaseProvider } from '@/contexts/database-context';
import { ExecutionProvider } from '@/contexts/execution-context';
import { ProjectProvider } from '@/contexts/project-context';
import { EditorProvider } from '@/contexts/editor-context';
import { Analytics } from '@vercel/analytics/next';

export const metadata: Metadata = {
  title: 'Codecraft IDE',
  description: "Open-source platform to modernize Informix 4GL systems with execution, 4GL <-> Python conversion, diagnostics, and a Python-powered web IDE."
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Source+Code+Pro:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body className={cn("font-body antialiased")}>
        <SessionProvider>
          <FileSystemProvider>
            <DatabaseProvider>
              <ExecutionProvider>
                <EditorProvider>
                  <ProjectProvider>
                    {children}
                    <Toaster />
                  </ProjectProvider>
                </EditorProvider>
              </ExecutionProvider>
            </DatabaseProvider>
          </FileSystemProvider>
        </SessionProvider>
        <Analytics />
      </body>
    </html>
  );
}
