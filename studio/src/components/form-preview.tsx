'use client';

import { useEffect, useState } from 'react';
import { API_BASE_URL } from '@/lib/api-client';

interface ScreenField {
  name: string;
  position: { row: number; column: number };
  width: number;
}

interface ScreenLine {
  row: number;
  content: string;
  fields: ScreenField[];
}

interface ScreenSection {
  width: number;
  height: number;
  lines: ScreenLine[];
}

interface FieldAttribute {
  screen_field: string;
  data_source: string;
  table_name: string | null;
  column_name: string | null;
  properties: Record<string, any>;
}

interface AttributesSection {
  fields: FieldAttribute[];
}

interface DatabaseDirective {
  database_name: string;
  options: string[];
}

interface InstructionsSection {
  instructions: Record<string, any>;
}

interface FormDefinition {
  database?: DatabaseDirective;
  screen?: ScreenSection;
  attributes?: AttributesSection;
  instructions?: InstructionsSection;
}

interface FormPreviewProps {
  content: string;
  onParsed?: (form: FormDefinition) => void;
}

export function FormPreview({ content, onParsed }: FormPreviewProps) {
  const [formData, setFormData] = useState<FormDefinition | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  useEffect(() => {
    const parseForm = async () => {
      if (!content || content.trim() === '') {
        setFormData(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE_URL}/api/parse-form`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content }),
        });

        const data = await response.json();

        if (data.status === 'error') {
          setError(data.message);
          setFormData(null);
        } else {
          setFormData(data.form);
          setValidationErrors(data.validation_errors || []);
          if (onParsed) {
            onParsed(data.form);
          }
        }
      } catch (err) {
        setError(`Failed to parse form: ${err instanceof Error ? err.message : String(err)}`);
        setFormData(null);
      } finally {
        setLoading(false);
      }
    };

    parseForm();
  }, [content, onParsed]);

  const renderScreenLine = (line: ScreenLine) => {
    // Create a character array for the line
    const chars: (string | JSX.Element)[] = [];
    let charIndex = 0;

    // Process the line content and replace field markers with input elements
    const fieldsByColumn = new Map<number, ScreenField>();
    line.fields.forEach((field) => {
      fieldsByColumn.set(field.position.column, field);
    });

    for (let i = 0; i < line.content.length; i++) {
      const char = line.content[i];

      // Check if this position starts a field
      const field = fieldsByColumn.get(i);
      if (field && line.content[i] === '[') {
        // Find the closing bracket
        const endBracket = line.content.indexOf(']', i);
        if (endBracket !== -1) {
          // Get field attributes if available
          const attr = formData?.attributes?.fields.find(
            (a) => a.screen_field === field.name
          );

          const isLabel = attr?.properties.widget === 'label';
          const isReadOnly = attr?.properties.noentry === true;

          chars.push(
            <span
              key={`field-${line.row}-${i}`}
              className={`inline-block border-b ${
                isLabel
                  ? 'border-gray-300 bg-gray-50 text-gray-600'
                  : isReadOnly
                  ? 'border-blue-300 bg-blue-50'
                  : 'border-green-500 bg-white'
              } px-1 font-mono text-sm`}
              style={{ width: `${field.width}ch` }}
              title={attr ? `${attr.data_source}${
                Object.keys(attr.properties).length > 0
                  ? '\n' + Object.entries(attr.properties)
                      .map(([k, v]) => `${k}: ${v}`)
                      .join('\n')
                  : ''
              }` : field.name}
            >
              {field.name}
            </span>
          );
          i = endBracket; // Skip to end of field marker
          charIndex = endBracket + 1;
          continue;
        }
      }

      chars.push(char);
      charIndex++;
    }

    return (
      <div key={`line-${line.row}`} className="font-mono text-sm whitespace-pre">
        {chars}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full p-4">
        <div className="text-gray-500">Parsing form...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded">
        <div className="font-semibold text-red-700">Parse Error</div>
        <div className="text-sm text-red-600 mt-1">{error}</div>
      </div>
    );
  }

  if (!formData) {
    return (
      <div className="flex items-center justify-center h-full p-4 text-gray-400">
        No form to preview
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with form metadata */}
      <div className="flex-shrink-0 bg-gray-50 border-b border-gray-200 p-3">
        <div className="flex items-center justify-between">
          <div>
            {formData.database && (
              <div className="text-sm">
                <span className="font-semibold text-gray-700">Database:</span>{' '}
                <span className="text-gray-900">{formData.database.database_name}</span>
                {formData.database.options.length > 0 && (
                  <span className="text-gray-500 ml-2">
                    ({formData.database.options.join(' ')})
                  </span>
                )}
              </div>
            )}
          </div>
          {validationErrors.length > 0 && (
            <div className="text-sm text-amber-600 font-semibold">
              ⚠️ {validationErrors.length} validation error{validationErrors.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      </div>

      {/* Form preview */}
      <div className="flex-1 overflow-auto p-4">
        {validationErrors.length > 0 && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded">
            <div className="font-semibold text-amber-800 mb-2">Validation Errors:</div>
            <ul className="list-disc list-inside text-sm text-amber-700 space-y-1">
              {validationErrors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          </div>
        )}

        {formData.screen && (
          <div className="bg-gray-900 p-4 rounded inline-block">
            <div className="bg-black text-green-400 p-3 rounded font-mono">
              {formData.screen.lines.map(renderScreenLine)}
            </div>
          </div>
        )}

        {/* Field attributes panel */}
        {formData.attributes && formData.attributes.fields.length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold text-gray-700 mb-3">Field Attributes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {formData.attributes.fields.map((attr, i) => (
                <div
                  key={i}
                  className="border border-gray-200 rounded p-3 bg-white hover:shadow-md transition-shadow"
                >
                  <div className="font-mono text-sm font-semibold text-gray-900 mb-1">
                    {attr.screen_field}
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    → {attr.data_source}
                  </div>
                  {Object.keys(attr.properties).length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {Object.entries(attr.properties).map(([key, value]) => (
                        <span
                          key={key}
                          className="inline-block bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded"
                        >
                          {key}: {String(value)}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Instructions */}
        {formData.instructions && Object.keys(formData.instructions.instructions).length > 0 && (
          <div className="mt-6">
            <h3 className="font-semibold text-gray-700 mb-3">Instructions</h3>
            <div className="border border-gray-200 rounded p-3 bg-gray-50">
              {Object.entries(formData.instructions.instructions).map(([key, value]) => (
                <div key={key} className="text-sm">
                  <span className="font-semibold text-gray-700">{key}:</span>{' '}
                  <span className="text-gray-900">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
