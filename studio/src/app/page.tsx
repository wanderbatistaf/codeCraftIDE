'use client';

import { TopBar } from '@/components/layout/top-bar';
import { FileExplorer } from '@/components/layout/file-explorer';
import { EditorArea } from '@/components/layout/editor-area';
import { BottomPanel } from '@/components/layout/bottom-panel';
import { useFileSystem } from '@/contexts/file-system-context';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { API_BASE_URL } from '@/lib/api-client';

export default function Home() {
  const { mode, remoteConfigName } = useFileSystem();
  const router = useRouter();
  const [authEnabled, setAuthEnabled] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Check if auth is enabled on backend
    fetch(`${API_BASE_URL}/api/health`)
      .then(res => res.json())
      .then(data => {
        setAuthEnabled(data.auth_enabled);

        // If auth is enabled, check if user is logged in
        if (data.auth_enabled) {
          const user = sessionStorage.getItem('user');
          if (!user) {
            router.push('/login');
          } else {
            setIsChecking(false);
          }
        } else {
          setIsChecking(false);
        }
      })
      .catch(() => {
        // Backend not available, allow access
        setIsChecking(false);
      });
  }, [router]);

  if (isChecking) {
    return (
      <div className="flex h-screen items-center justify-center bg-background text-foreground">
        <div className="text-center">
          <div className="text-xl mb-2">Loading...</div>
          <div className="text-sm text-muted-foreground">Checking authentication status</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-background text-foreground font-body">
      <TopBar />
      <main className="flex flex-1 overflow-hidden">
        <FileExplorer key={`${mode}-${remoteConfigName || 'local'}`} />
        <div className="flex flex-1 flex-col overflow-hidden">
          <EditorArea />
          <BottomPanel />
        </div>
      </main>
    </div>
  );
}
