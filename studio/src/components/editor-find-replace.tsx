"use client";

import { useState, useEffect } from "react";
import { Search, X, ChevronDown, ChevronUp, Replace, ReplaceAll } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface EditorFindReplaceProps {
  editor: any; // Monaco editor instance
  monaco: any; // Monaco module
  isOpen: boolean;
  onClose: () => void;
  mode: "find" | "replace";
}

export function EditorFindReplace({
  editor,
  monaco,
  isOpen,
  onClose,
  mode: initialMode
}: EditorFindReplaceProps) {
  const [mode, setMode] = useState<"find" | "replace">(initialMode);
  const [findText, setFindText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [wholeWord, setWholeWord] = useState(false);
  const [useRegex, setUseRegex] = useState(false);
  const [currentMatch, setCurrentMatch] = useState(0);
  const [totalMatches, setTotalMatches] = useState(0);

  // Find matches in the editor
  const findMatches = () => {
    if (!editor || !monaco || !findText) {
      setTotalMatches(0);
      setCurrentMatch(0);
      return [];
    }

    const model = editor.getModel();
    if (!model) return [];

    let searchString = findText;
    if (!useRegex) {
      searchString = findText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    const flags = caseSensitive ? 'g' : 'gi';
    const wordBoundary = wholeWord ? '\\b' : '';
    const regex = new RegExp(`${wordBoundary}${searchString}${wordBoundary}`, flags);

    const matches = model.findMatches(
      searchString,
      true,
      useRegex,
      caseSensitive,
      wholeWord ? model.getWordAtPosition.toString() : null,
      true
    );

    setTotalMatches(matches.length);
    return matches;
  };

  // Navigate to next match
  const findNext = () => {
    const matches = findMatches();
    if (matches.length === 0) return;

    const position = editor.getPosition();
    let nextMatch = matches.find(m =>
      m.range.startLineNumber > position.lineNumber ||
      (m.range.startLineNumber === position.lineNumber && m.range.startColumn > position.column)
    );

    if (!nextMatch) {
      nextMatch = matches[0]; // Wrap around
    }

    editor.setSelection(nextMatch.range);
    editor.revealRangeInCenter(nextMatch.range);

    const index = matches.indexOf(nextMatch);
    setCurrentMatch(index + 1);
  };

  // Navigate to previous match
  const findPrevious = () => {
    const matches = findMatches();
    if (matches.length === 0) return;

    const position = editor.getPosition();
    let prevMatch = matches.reverse().find(m =>
      m.range.startLineNumber < position.lineNumber ||
      (m.range.startLineNumber === position.lineNumber && m.range.startColumn < position.column)
    );

    if (!prevMatch) {
      prevMatch = matches[0]; // Wrap around
    }

    editor.setSelection(prevMatch.range);
    editor.revealRangeInCenter(prevMatch.range);

    const index = matches.reverse().indexOf(prevMatch);
    setCurrentMatch(index + 1);
  };

  // Replace current match
  const replaceCurrent = () => {
    const selection = editor.getSelection();
    if (!selection) return;

    editor.executeEdits('replace', [{
      range: selection,
      text: replaceText
    }]);

    findNext();
  };

  // Replace all matches
  const replaceAllMatches = () => {
    const matches = findMatches();
    if (matches.length === 0) return;

    const edits = matches.map(match => ({
      range: match.range,
      text: replaceText
    }));

    editor.executeEdits('replace-all', edits);
    setTotalMatches(0);
    setCurrentMatch(0);
  };

  // Update matches when find text changes
  useEffect(() => {
    if (findText) {
      findMatches();
    }
  }, [findText, caseSensitive, wholeWord, useRegex]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'Enter') {
        if (e.shiftKey) {
          findPrevious();
        } else {
          findNext();
        }
        e.preventDefault();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, findText]);

  if (!isOpen) return null;

  return (
    <div className="absolute top-2 right-4 z-50 bg-background border rounded-lg shadow-lg p-3 w-[400px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex gap-2">
          <Button
            variant={mode === "find" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMode("find")}
          >
            Find
          </Button>
          <Button
            variant={mode === "replace" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMode("replace")}
          >
            Replace
          </Button>
        </div>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Find Input */}
      <div className="flex gap-2 mb-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground" />
          <Input
            value={findText}
            onChange={(e) => setFindText(e.target.value)}
            placeholder="Find"
            className="pl-7 h-8 text-sm"
            autoFocus
          />
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={findPrevious}>
          <ChevronUp className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={findNext}>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </div>

      {/* Replace Input */}
      {mode === "replace" && (
        <div className="flex gap-2 mb-2">
          <Input
            value={replaceText}
            onChange={(e) => setReplaceText(e.target.value)}
            placeholder="Replace"
            className="h-8 text-sm"
          />
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={replaceCurrent} title="Replace">
            <Replace className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={replaceAllMatches} title="Replace All">
            <ReplaceAll className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Options */}
      <div className="flex items-center gap-2 text-xs">
        <Button
          variant={caseSensitive ? "default" : "outline"}
          size="sm"
          className="h-6 text-xs"
          onClick={() => setCaseSensitive(!caseSensitive)}
        >
          Aa
        </Button>
        <Button
          variant={wholeWord ? "default" : "outline"}
          size="sm"
          className="h-6 text-xs"
          onClick={() => setWholeWord(!wholeWord)}
        >
          Ab
        </Button>
        <Button
          variant={useRegex ? "default" : "outline"}
          size="sm"
          className="h-6 text-xs"
          onClick={() => setUseRegex(!useRegex)}
        >
          .*
        </Button>
        {totalMatches > 0 && (
          <span className="ml-auto text-muted-foreground">
            {currentMatch} of {totalMatches}
          </span>
        )}
      </div>
    </div>
  );
}
