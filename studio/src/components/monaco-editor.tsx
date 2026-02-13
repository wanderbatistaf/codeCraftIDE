'use client';

import { useRef, useEffect, useCallback, useState } from 'react';
import MonacoEditor from '@monaco-editor/react';
import type { OnMount } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { apiClient, type Diagnostic, type CodeAction } from '../lib/api-client';
import { EditorFindReplace } from './editor-find-replace';

interface MonacoEditorProps {
  value: string;
  onChange: (value: string) => void;
  onEditorReady?: (editor: editor.IStandaloneCodeEditor, monaco: typeof import('monaco-editor')) => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
  readOnly?: boolean;
  language?: string; // Optional language override
  enableDiagnostics?: boolean; // Enable automatic diagnostics
}

// Helper function to map diagnostic severity to Monaco severity
function getSeverity(monaco: typeof import('monaco-editor'), severity: string): number {
  switch (severity) {
    case 'error':
      return monaco.MarkerSeverity.Error;
    case 'warning':
      return monaco.MarkerSeverity.Warning;
    case 'info':
      return monaco.MarkerSeverity.Info;
    case 'hint':
      return monaco.MarkerSeverity.Hint;
    default:
      return monaco.MarkerSeverity.Info;
  }
}

export function FGLMonacoEditor({
  value,
  onChange,
  onKeyDown,
  onEditorReady,
  readOnly = false,
  language = 'fgl',
  enableDiagnostics = true
}: MonacoEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof import('monaco-editor') | null>(null);
  const updateDiagnosticsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Find/Replace state
  const [findReplaceOpen, setFindReplaceOpen] = useState(false);
  const [findReplaceMode, setFindReplaceMode] = useState<"find" | "replace">("find");

  // Fetch and apply diagnostics
  const updateDiagnostics = useCallback(async (code: string, immediate = false) => {
    if (!enableDiagnostics || !monacoRef.current || !editorRef.current || language !== 'fgl') {
      return;
    }

    // Clear any pending timeout if this is an immediate update
    if (immediate && updateDiagnosticsTimeoutRef.current) {
      clearTimeout(updateDiagnosticsTimeoutRef.current);
      updateDiagnosticsTimeoutRef.current = null;
    }

    try {
      const response = await apiClient.getDiagnostics({ code });

      if (response.status === 'success' && response.diagnostics) {
        const monaco = monacoRef.current;
        const model = editorRef.current.getModel();

        if (!model) return;

        // Convert diagnostics to Monaco markers
        const markers: editor.IMarkerData[] = response.diagnostics.map((diag: Diagnostic) => ({
          severity: getSeverity(monaco, diag.severity),
          message: diag.message,
          startLineNumber: diag.line,
          startColumn: diag.column,
          endLineNumber: diag.end_line || diag.line,
          endColumn: diag.end_column || diag.column + 1,
        }));

        // Set markers
        monaco.editor.setModelMarkers(model, 'fgl-diagnostics', markers);
      }
    } catch (error) {
      console.error('Failed to fetch diagnostics:', error);
    }
  }, [enableDiagnostics, language]);

  // Debounced diagnostics update
  useEffect(() => {
    if (!enableDiagnostics || language !== 'fgl') return;

    updateDiagnosticsTimeoutRef.current = setTimeout(() => {
      updateDiagnostics(value, false);
    }, 500); // 500ms debounce

    return () => {
      if (updateDiagnosticsTimeoutRef.current) {
        clearTimeout(updateDiagnosticsTimeoutRef.current);
      }
    };
  }, [value, enableDiagnostics, language, updateDiagnostics]);

  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    // Notify parent component that editor is ready
    onEditorReady?.(editor, monaco);

    // Register 4GL language
    monaco.languages.register({ id: 'fgl' });

    // Define 4GL tokens
    monaco.languages.setMonarchTokensProvider('fgl', {
      defaultToken: '',
      symbols: /[=><!~?:&|+\-*\/\^%]+/,
      blockOpen: ['IF', 'FOR', 'WHILE', 'FOREACH', 'CASE', 'FUNCTION', 'MAIN'],
      blockMiddle: ['ELSE', 'ELSEIF', 'ELIF', 'WHEN', 'OTHERWISE'],
      blockClose: ['ENDIF', 'ENDFOR', 'ENDWHILE', 'ENDFOREACH', 'ENDCASE', 'ENDFUNCTION'],
      keywords: [
        'END', 'THEN', 'RETURN', 'LET', 'DEFINE', 'CALL', 'DISPLAY', 'INPUT', 'PROMPT', 'MENU',
        'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'FROM', 'WHERE', 'INTO', 'VALUES', 'SET',
        'DATABASE', 'BEGIN', 'WORK', 'COMMIT', 'ROLLBACK', 'PREPARE', 'EXECUTE', 'DECLARE',
        'CURSOR', 'OPEN', 'FETCH', 'CLOSE', 'CONTINUE', 'EXIT', 'SLEEP', 'RUN', 'WHENEVER',
        'ERROR', 'NOT', 'FOUND', 'SQLERROR', 'SQLWARNING', 'NOTFOUND', 'TO', 'STEP', 'BY', 'AS',
        'IN', 'OUT', 'AND', 'OR'
      ],
      typeKeywords: [
        'INTEGER', 'SMALLINT', 'DECIMAL', 'MONEY', 'FLOAT', 'REAL', 'CHAR', 'VARCHAR', 'DATE',
        'DATETIME', 'INTERVAL', 'BOOLEAN', 'BYTE', 'TEXT', 'SERIAL', 'BIGSERIAL', 'INT8', 'BIGINT'
      ],
      operators: [
        '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
        '&&', '||', '++', '--', '+', '-', '*', '/', '&', '|', '^', '%',
        '<<', '>>', '>>>', '+=', '-=', '*=', '/=', '&=', '|=', '^=',
        '%=', '<<=', '>>=', '>>>='
      ],
      tokenizer: {
  root: [
    [/\b(END)\s+(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)\b/i, 'keyword.block.close'],
    [/\b(ENDIF|ENDFOR|ENDWHILE|ENDFOREACH|ENDCASE|ENDFUNCTION)\b/i, 'keyword.block.close'],
    [/\b(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)\b/i, 'keyword.block.open'],
    [/\b(ELSE|ELSEIF|ELIF|WHEN|OTHERWISE)\b/i, 'keyword.block.middle'],
    [/[a-z_$][\w$]*/, {
      cases: {
        '@typeKeywords': 'keyword.type',
        '@keywords': 'keyword',
        '@default': 'identifier'
      }
    }],
    { include: '@whitespace' },
    [/[{}()\[\]]/, '@brackets'],
    // substitui [<>](?!@symbols) por apenas operadores individuais
    [/[<>]/, 'operator'],
    [/[=><!~?:&|+\-*\/\^%]+/, 'operator'],
    [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
    [/0[xX][0-9a-fA-F]+/, 'number.hex'],
    [/\d+/, 'number'],
    [/[;,.]/, 'delimiter'],
    [/"([^"\\]|\\.)*$/, 'string.invalid'],
    [/"/, { token: 'string.quote', bracket: '@open', next: '@string' }],
    [/'([^'\\]|\\.)*$/, 'string.invalid'],
    [/'/, { token: 'string.quote', bracket: '@open', next: '@stringSingle' }]
  ],
  string: [
    [/[^\\"]+/, 'string'],
    [/\\./, 'string.escape.invalid'],
    [/"/, { token: 'string.quote', bracket: '@close', next: '@pop' }]
  ],
  stringSingle: [
    [/[^\\']+/, 'string'],
    [/\\./, 'string.escape.invalid'],
    [/'/, { token: 'string.quote', bracket: '@close', next: '@pop' }]
  ],
  whitespace: [
    [/[ \t\r\n]+/, 'white'],
    [/#.*$/, 'comment'],
    [/--.*$/, 'comment'],
    [/{/, 'comment', '@comment']
  ],
  comment: [
    [/[^}]+/, 'comment'],
    [/}/, 'comment', '@pop'],
    [/{/, 'comment']
  ]
}

    });

    // Register .per (Querix form) language
    monaco.languages.register({ id: 'per' });

    // Define .per tokens
    monaco.languages.setMonarchTokensProvider('per', {
      defaultToken: '',
      keywords: [
        'DATABASE', 'SCREEN', 'ATTRIBUTES', 'INSTRUCTIONS', 'END',
        'FORMONLY', 'WITHOUT', 'NULL', 'INPUT', 'DELIMITERS',
        'UPSHIFT', 'DOWNSHIFT', 'NOENTRY', 'TYPE', 'WIDGET',
        'WORDWRAP', 'REQUIRED', 'SCREEN_RECORD'
      ],
      typeKeywords: [
        'CHAR', 'VARCHAR', 'INTEGER', 'SMALLINT', 'DECIMAL', 'MONEY',
        'FLOAT', 'REAL', 'DATE', 'DATETIME', 'INTERVAL', 'BOOLEAN',
        'BYTE', 'TEXT', 'SERIAL', 'BIGSERIAL'
      ],
      tokenizer: {
        root: [
          // Keywords
          [/\b(DATABASE|SCREEN|ATTRIBUTES|INSTRUCTIONS|END|FORMONLY)\b/i, 'keyword'],
          [/\b(WITHOUT|NULL|INPUT|DELIMITERS|UPSHIFT|DOWNSHIFT|NOENTRY)\b/i, 'keyword'],
          [/\b(TYPE|WIDGET|WORDWRAP|REQUIRED|SCREEN_RECORD)\b/i, 'keyword'],

          // Type keywords
          [/\b(CHAR|VARCHAR|INTEGER|SMALLINT|DECIMAL|MONEY|FLOAT|REAL)\b/i, 'keyword.type'],
          [/\b(DATE|DATETIME|INTERVAL|BOOLEAN|BYTE|TEXT|SERIAL)\b/i, 'keyword.type'],

          // Field markers in screen section
          [/\[([a-z_][a-z0-9_]*)\]/i, 'variable.field'],

          // Identifiers
          [/[a-z_][\w]*/, 'identifier'],

          // Whitespace
          { include: '@whitespace' },

          // Delimiters
          [/[{}()\[\]]/, '@brackets'],
          [/[=,;.]/, 'delimiter'],

          // Strings
          [/"([^"\\]|\\.)*$/, 'string.invalid'],
          [/"/, { token: 'string.quote', bracket: '@open', next: '@string' }],

          // Numbers
          [/\d+/, 'number'],

          // Layout characters
          [/\\g/, 'keyword.special'],
        ],
        string: [
          [/[^\\"]+/, 'string'],
          [/\\./, 'string.escape'],
          [/"/, { token: 'string.quote', bracket: '@close', next: '@pop' }]
        ],
        whitespace: [
          [/[ \t\r\n]+/, 'white'],
          [/#.*$/, 'comment'],
          [/--.*$/, 'comment'],
        ]
      }
    });

    // Semantic highlighting (blocks)
    const legend = {
      tokenTypes: ['keyword.block.open.matched', 'keyword.block.middle.matched', 'keyword.block.close.matched'],
      tokenModifiers: []
    };

    // Create an event emitter for semantic token changes
    const semanticTokensEmitter = new monaco.Emitter<void>();

    monaco.languages.registerDocumentSemanticTokensProvider('fgl', {
      getLegend: () => legend,
      onDidChangeSemanticTokens: semanticTokensEmitter.event,
      provideDocumentSemanticTokens: (model) => {
        try {
          const startLineCount = model.getLineCount();
          const lines = model.getLinesContent();

          // Collect all tokens first
          const rawTokens: Array<{ line: number; char: number; length: number; type: number }> = [];
          const blocks: { type: string; startLine: number; endLine?: number; matched: boolean }[] = [];
          const blockStack: { type: string; line: number }[] = [];

          lines.forEach((line, lineIndex) => {
            if (lineIndex >= startLineCount) return;

            const upper = line.toUpperCase();
            const openMatch = upper.match(/\b(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)\b/);
            if (openMatch) blockStack.push({ type: openMatch[1], line: lineIndex });

            const closeMatch = upper.match(/\b(END\s+(?:IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)|ENDIF|ENDFOR|ENDWHILE|ENDFOREACH|ENDCASE|ENDFUNCTION)\b/);
            if (closeMatch && blockStack.length) {
              const openBlock = blockStack.pop()!;
              blocks.push({ type: openBlock.type, startLine: openBlock.line, endLine: lineIndex, matched: true });
            }
          });

          blockStack.forEach(block => blocks.push({ type: block.type, startLine: block.line, matched: false }));

          const matchedLines = new Set(
            blocks
              .filter(b => b.matched && b.startLine < startLineCount && (b.endLine === undefined || b.endLine < startLineCount))
              .flatMap(b => [b.startLine, b.endLine!].filter(line => line !== undefined && line < startLineCount))
          );

          lines.forEach((line, lineIndex) => {
            if (lineIndex >= startLineCount || !matchedLines.has(lineIndex)) return;

            const upper = line.toUpperCase();

            let match = upper.match(/\b(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)\b/);
            if (match && match.index !== undefined) {
              rawTokens.push({ line: lineIndex, char: match.index, length: match[1].length, type: 0 });
            }

            match = upper.match(/\b(ELSE|ELSEIF|ELIF|WHEN|OTHERWISE)\b/);
            if (match && match.index !== undefined) {
              rawTokens.push({ line: lineIndex, char: match.index, length: match[1].length, type: 1 });
            }

            match = upper.match(/\b(END\s+(?:IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)|ENDIF|ENDFOR|ENDWHILE|ENDFOREACH|ENDCASE|ENDFUNCTION)\b/);
            if (match && match.index !== undefined) {
              rawTokens.push({ line: lineIndex, char: match.index, length: match[0].length, type: 2 });
            }
          });

          // Sort tokens by line then by character position
          rawTokens.sort((a, b) => a.line !== b.line ? a.line - b.line : a.char - b.char);

          // Convert to delta-encoded format required by Monaco
          const tokens: number[] = [];
          let prevLine = 0;
          let prevChar = 0;

          for (const token of rawTokens) {
            // Validate token is still within bounds
            if (token.line >= startLineCount) continue;

            const deltaLine = token.line - prevLine;
            const deltaChar = deltaLine === 0 ? token.char - prevChar : token.char;

            tokens.push(deltaLine, deltaChar, token.length, token.type, 0);

            prevLine = token.line;
            prevChar = token.char;
          }

          // Final validation
          const endLineCount = model.getLineCount();
          if (startLineCount !== endLineCount) {
            return { data: new Uint32Array([]) };
          }

          return { data: new Uint32Array(tokens) };
        } catch (error) {
          console.error('Error generating semantic tokens:', error);
          return { data: new Uint32Array([]) };
        }
      },
      releaseDocumentSemanticTokens: () => {}
    });

    // Listen to model content changes and invalidate semantic tokens
    const model = editor.getModel();
    if (model) {
      let lastChangeTime = 0;
      let lastChangeCount = 0;
      let diagnosticsUpdateTimeout: NodeJS.Timeout | null = null;
      let semanticTokensTimeout: NodeJS.Timeout | null = null;

      model.onDidChangeContent((e) => {
        const currentValue = model.getValue();
        lastChangeCount++;
        const changeId = lastChangeCount;

        // Clear any pending semantic tokens update
        if (semanticTokensTimeout) {
          clearTimeout(semanticTokensTimeout);
        }

        // Invalidate semantic tokens with a longer delay to ensure model is fully stable
        // Only fire if no new changes occurred in the meantime
        semanticTokensTimeout = setTimeout(() => {
          if (changeId === lastChangeCount) {
            // No new changes, safe to recalculate tokens
            semanticTokensEmitter.fire();
          }
        }, 500); // Increased delay to ensure stability

        // Update diagnostics immediately for quick fixes (small changes)
        // or with debounce for typing (frequent changes)
        const now = Date.now();
        const timeSinceLastChange = now - lastChangeTime;
        lastChangeTime = now;

        // Clear any pending diagnostics update
        if (diagnosticsUpdateTimeout) {
          clearTimeout(diagnosticsUpdateTimeout);
        }

        // If this is a single change (likely a quick fix), update immediately
        // Otherwise debounce to avoid too many requests while typing
        if (e.changes.length === 1 && timeSinceLastChange > 300) {
          // Immediate update for quick fixes
          setTimeout(() => {
            if (editorRef.current) {
              const latestValue = editorRef.current.getValue();
              updateDiagnostics(latestValue, true);
            }
          }, 300);
        } else {
          // Debounced update for typing
          diagnosticsUpdateTimeout = setTimeout(() => {
            if (editorRef.current) {
              const latestValue = editorRef.current.getValue();
              updateDiagnostics(latestValue, true);
            }
          }, 500);
        }
      });
    }

    // Language configuration
    monaco.languages.setLanguageConfiguration('fgl', {
      brackets: [['(', ')'], ['{', '}'], ['[', ']']],
      autoClosingPairs: [
        { open: '(', close: ')' },
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '"', close: '"' },
        { open: "'", close: "'" }
      ],
      surroundingPairs: [
        { open: '(', close: ')' },
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '"', close: '"' },
        { open: "'", close: "'" }
      ],
      indentationRules: {
        increaseIndentPattern: /^\s*(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN|ELSE|ELSEIF|ELIF|WHEN|OTHERWISE)\b/i,
        decreaseIndentPattern: /^\s*(END\s+(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)|ENDIF|ENDFOR|ENDWHILE|ENDFOREACH|ENDCASE|ENDFUNCTION|ELSE|ELSEIF|ELIF|WHEN|OTHERWISE)\b/i
      },
      onEnterRules: [
        {
          beforeText: /^\s*(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)\b.*$/i,
          action: { indentAction: monaco.languages.IndentAction.Indent }
        },
        {
          beforeText: /^\s*(ELSE|ELSEIF|ELIF|WHEN|OTHERWISE)\b.*$/i,
          afterText: /^\s*(END|ENDIF|ENDFOR|ENDWHILE|ENDFOREACH|ENDCASE|ENDFUNCTION).*$/i,
          action: { indentAction: monaco.languages.IndentAction.IndentOutdent }
        },
        {
          beforeText: /^\s*(END\s+(IF|FOR|WHILE|FOREACH|CASE|FUNCTION|MAIN)|ENDIF|ENDFOR|ENDWHILE|ENDFOREACH|ENDCASE|ENDFUNCTION)\b.*$/i,
          action: { indentAction: monaco.languages.IndentAction.Outdent }
        }
      ]
    });

    // Theme
    monaco.editor.defineTheme('fgl-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '569CD6', fontStyle: 'bold' },
        { token: 'keyword.type', foreground: '4EC9B0' },
        { token: 'keyword.block.open', foreground: 'C586C0', fontStyle: 'bold' },
        { token: 'keyword.block.middle', foreground: 'C586C0', fontStyle: 'bold' },
        { token: 'keyword.block.close', foreground: 'C586C0', fontStyle: 'bold' },
        { token: 'keyword.block.open.matched', foreground: '4EC9B0', fontStyle: 'bold' },
        { token: 'keyword.block.middle.matched', foreground: 'C586C0', fontStyle: 'bold' },
        { token: 'keyword.block.close.matched', foreground: '4EC9B0', fontStyle: 'bold' },
        { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
        { token: 'string', foreground: 'CE9178' },
        { token: 'number', foreground: 'B5CEA8' },
        { token: 'operator', foreground: 'D4D4D4' }
      ],
      colors: {
        'editor.background': '#1e1e1e',
        'editor.foreground': '#d4d4d4',
        'editorLineNumber.foreground': '#858585',
        'editorLineNumber.activeForeground': '#c6c6c6',
        'editor.selectionBackground': '#264f78',
        'editor.inactiveSelectionBackground': '#3a3d41',
        'editor.lineHighlightBackground': '#2a2a2a',
        'editorBracketMatch.background': '#0064001a',
        'editorBracketMatch.border': '#888888',
        'editorIndentGuide.background': '#404040',
        'editorIndentGuide.activeBackground': '#707070'
      }
    });

    monaco.editor.setTheme('fgl-dark');

    // Register code actions provider for quick fixes
    if (enableDiagnostics) {
      monaco.languages.registerCodeActionProvider('fgl', {
        provideCodeActions: async (model, range, context) => {
          const actions: any[] = [];

          try {
            // Get code actions from the backend
            const code = model.getValue();
            const response = await apiClient.getCodeActions({
              code,
              line: range.startLineNumber,
              column: range.startColumn,
            });

            if (response.status === 'success' && response.actions) {
              response.actions.forEach((action: CodeAction) => {
                actions.push({
                  title: action.title,
                  diagnostics: context.markers,
                  kind: 'quickfix',
                  edit: {
                    edits: [
                      {
                        resource: model.uri,
                        textEdit: {
                          range: {
                            startLineNumber: action.insert_line,
                            startColumn: action.insert_column || 1,
                            endLineNumber: action.insert_line,
                            endColumn: action.insert_column || 1,
                          },
                          text: action.new_text,
                        },
                      },
                    ],
                  },
                  isPreferred: true,
                });
              });
            }
          } catch (error) {
            console.error('Failed to get code actions:', error);
          }

          return {
            actions,
            dispose: () => {},
          };
        },
      });
    }

    // Run initial diagnostics
    if (enableDiagnostics && language === 'fgl') {
      updateDiagnostics(value);
    }

    // Keyboard events
    editor.onKeyDown((e) => {
      // Handle Ctrl+F (Find) and Ctrl+H (Replace)
      if ((e.ctrlKey || e.metaKey) && e.code === 'KeyF') {
        e.preventDefault();
        e.stopPropagation();
        setFindReplaceMode('find');
        setFindReplaceOpen(true);
        return;
      }

      if ((e.ctrlKey || e.metaKey) && e.code === 'KeyH') {
        e.preventDefault();
        e.stopPropagation();
        setFindReplaceMode('replace');
        setFindReplaceOpen(true);
        return;
      }

      // Call custom onKeyDown handler if provided
      if (onKeyDown) {
        const syntheticEvent = {
          key: e.browserEvent.key,
          code: e.browserEvent.code,
          ctrlKey: e.ctrlKey,
          metaKey: e.metaKey,
          shiftKey: e.shiftKey,
          altKey: e.altKey,
          preventDefault: () => e.preventDefault(),
          stopPropagation: () => e.stopPropagation(),
        } as unknown as React.KeyboardEvent;
        onKeyDown(syntheticEvent);
      }
    });
  };

  return (
    <div className="h-full w-full relative">
      <MonacoEditor
        height="100%"
        language={language}
        value={value}
        onChange={(v) => onChange(v || '')}
        onMount={handleEditorDidMount}
        options={{
          readOnly,
          minimap: { enabled: true },
          fontSize: 14,
          lineNumbers: 'on',
          roundedSelection: false,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 2,
          insertSpaces: true,
          wordWrap: 'off',
          folding: true,
          foldingStrategy: 'indentation',
          showFoldingControls: 'always',
          'semanticHighlighting.enabled': true,
          bracketPairColorization: { enabled: true, independentColorPoolPerBracketType: true },
          guides: { bracketPairs: true, bracketPairsHorizontal: 'active', highlightActiveBracketPair: true, indentation: true, highlightActiveIndentation: true },
          matchBrackets: 'always',
          stickyScroll: { enabled: true, maxLineCount: 5 },
          renderLineHighlight: 'all',
          occurrencesHighlight: 'singleFile',
          selectionHighlight: true,
          scrollbar: { vertical: 'visible', horizontal: 'visible', useShadows: true, verticalHasArrows: false, horizontalHasArrows: false, verticalScrollbarSize: 10, horizontalScrollbarSize: 10 },
          fixedOverflowWidgets: true,
          find: {
            addExtraSpaceOnTop: false,
            autoFindInSelection: 'never',
            seedSearchStringFromSelection: 'never'
          }
        }}
      />
      <EditorFindReplace
        editor={editorRef.current}
        monaco={monacoRef.current}
        isOpen={findReplaceOpen}
        onClose={() => setFindReplaceOpen(false)}
        mode={findReplaceMode}
      />
    </div>
  );
}
