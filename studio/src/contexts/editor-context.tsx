'use client';

import { createContext, useContext, useRef, ReactNode } from 'react';
import type { editor } from 'monaco-editor';

interface EditorContextType {
  editorRef: React.MutableRefObject<editor.IStandaloneCodeEditor | null>;
  monacoRef: React.MutableRefObject<typeof import('monaco-editor') | null>;
  goToLine: (lineNumber: number) => void;
}

const EditorContext = createContext<EditorContextType | null>(null);

export function EditorProvider({ children }: { children: ReactNode }) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof import('monaco-editor') | null>(null);

  const goToLine = (lineNumber: number) => {
    if (!editorRef.current) return;

    // Reveal and select the line
    editorRef.current.revealLineInCenter(lineNumber);
    editorRef.current.setPosition({ lineNumber, column: 1 });
    editorRef.current.focus();

    // Select the entire line
    const model = editorRef.current.getModel();
    if (model) {
      const lineLength = model.getLineLength(lineNumber);
      editorRef.current.setSelection({
        startLineNumber: lineNumber,
        startColumn: 1,
        endLineNumber: lineNumber,
        endColumn: lineLength + 1
      });
    }
  };

  return (
    <EditorContext.Provider value={{ editorRef, monacoRef, goToLine }}>
      {children}
    </EditorContext.Provider>
  );
}

export function useEditor() {
  const context = useContext(EditorContext);
  if (!context) {
    throw new Error('useEditor must be used within EditorProvider');
  }
  return context;
}
