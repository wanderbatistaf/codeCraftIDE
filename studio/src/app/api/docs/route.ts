import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

const DOCS_BASE_PATH = path.join(process.cwd(), 'Documentation');

// GET /api/docs - List available documentation files
// GET /api/docs?lang=en-us - List docs for specific language
// GET /api/docs?lang=en-us&file=00-Overview.md - Get specific file content
export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const lang = searchParams.get('lang');
  const file = searchParams.get('file');

  try {
    // If no lang specified, return available languages
    if (!lang) {
      const languages = fs.readdirSync(DOCS_BASE_PATH)
        .filter(item => {
          const itemPath = path.join(DOCS_BASE_PATH, item);
          return fs.statSync(itemPath).isDirectory();
        });

      return NextResponse.json({ languages });
    }

    const langPath = path.join(DOCS_BASE_PATH, lang);

    // Check if language directory exists
    if (!fs.existsSync(langPath)) {
      return NextResponse.json({ error: 'Language not found' }, { status: 404 });
    }

    // If no file specified, return list of files for the language
    if (!file) {
      const files = fs.readdirSync(langPath)
        .filter(f => f.endsWith('.md') && /^\d{2}-/.test(f)) // Only files starting with XX-
        .sort()
        .map(f => {
          // Extract title from filename (e.g., "00-Overview.md" -> "Overview")
          const nameWithoutExt = f.replace('.md', '');
          const parts = nameWithoutExt.split('-');
          const number = parts[0];
          // Join remaining parts and convert dashes/underscores to spaces, capitalize properly
          const title = parts.slice(1)
            .join(' ')
            .replace(/[-_]/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
          return {
            filename: f,
            number,
            title,
            displayTitle: `${number}. ${title}`,
          };
        });

      return NextResponse.json({ files });
    }

    // Return specific file content
    const filePath = path.join(langPath, file);

    // Security check - prevent directory traversal
    if (!filePath.startsWith(DOCS_BASE_PATH)) {
      return NextResponse.json({ error: 'Invalid path' }, { status: 400 });
    }

    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }

    const content = fs.readFileSync(filePath, 'utf-8');

    return NextResponse.json({ content, filename: file });
  } catch (error: any) {
    console.error('Documentation API error:', error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
