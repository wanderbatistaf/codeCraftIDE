"use client";

import * as React from "react";
import { useState, useEffect, useMemo, useId, useRef } from "react";
import { cn } from "@/lib/utils";
import type { LyciaComponent, LyciaFormData } from "@/lib/api-client";

interface LyciaFormPreviewProps {
  formData: LyciaFormData | null;
  cssContent?: string;
  scale?: number;
  showGrid?: boolean;
  showShell?: boolean;
  captureHtml?: boolean;
  onHtmlCapture?: (html: string) => void;
  selectedComponent?: string | null;
  onSelectComponent?: (identifier: string | null) => void;
}

// Character unit size in pixels (approximate)
const CHAR_WIDTH = 8;
const CHAR_HEIGHT = 18;

// Lycia component types that should be converted to class selectors
const LYCIA_COMPONENT_TYPES = [
  "CoordPanel", "GridPanel", "Label", "TextField", "Button",
  "CheckBox", "ComboBox", "Separator", "Table", "Tree",
  "Canvas", "Image", "Group", "ScrollGrid", "Folder"
];

export function LyciaFormPreview({
  formData,
  cssContent,
  scale = 1,
  showGrid = false,
  showShell = true,
  captureHtml = false,
  onHtmlCapture,
  selectedComponent,
  onSelectComponent,
}: LyciaFormPreviewProps) {
  // Generate unique ID for scoping CSS
  const scopeId = useId().replace(/:/g, "");
  const previewRef = useRef<HTMLDivElement | null>(null);

  // Process CSS to scope it to this preview and convert element selectors to class selectors
  const scopedCss = useMemo(() => {
    if (!cssContent) return "";

    // Remove comments
    let processed = cssContent.replace(/\/\*[\s\S]*?\*\//g, "");

    // Convert Lycia component type selectors to class selectors
    // e.g., "CoordPanel {" becomes ".CoordPanel {"
    // e.g., "TextField[noEntry="true"]" becomes ".TextField[data-noentry="true"]"
    LYCIA_COMPONENT_TYPES.forEach(type => {
      // Match the type name at word boundary, not already a class
      const regex = new RegExp(`(?<![.#])\\b(${type})\\b(?![\\w-])`, 'g');
      processed = processed.replace(regex, '.$1');
    });

    // Convert attribute selectors to data-attribute selectors (lowercase)
    // e.g., [noEntry="true"] becomes [data-noentry="true"]
    // e.g., [isDynamic="true"] becomes [data-isdynamic="true"]
    // e.g., [separatorType="Vertical"] becomes [data-separatortype="Vertical"]
    // e.g., [identifier^="load_"] becomes [data-identifier^="load_"]
    processed = processed.replace(
      /\[(\w+)([~|^$*]?=)/g,
      (match, attr, operator) => {
        const lowerAttr = attr.toLowerCase();
        return `[data-${lowerAttr}${operator}`;
      }
    );

    // Scope the CSS - prepend each rule with our scope
    processed = processed.replace(
      /([^{}]+)(\{[^{}]*\})/g,
      (match, selectors, block) => {
        const scopedSelectors = selectors
          .split(",")
          .map((s: string) => `.lycia-preview-${scopeId} ${s.trim()}`)
          .join(", ");
        return scopedSelectors + block;
      }
    );

    return processed;
  }, [cssContent, scopeId]);

  // Default CSS styles - Lycia-accurate (no padding on containers!)
  const defaultStyles = `
    .lycia-preview-${scopeId} {
      font-family: Arial, "Helvetica Neue", sans-serif;
      font-size: 10px;
      color: #000;
    }
    .lycia-preview-${scopeId} .lycia-form-container {
      background: #f8f9fa;
    }
    /* Containers - NO PADDING to preserve absolute positioning */
    .lycia-preview-${scopeId} .CoordPanel,
    .lycia-preview-${scopeId} .GridPanel {
      background-color: #f0f0f0;
      /* NO padding - would break absolute positioning */
    }
    /* Labels - Lycia default style */
    .lycia-preview-${scopeId} .Label {
      font-weight: normal;
      color: #000;
      display: flex;
      align-items: center;
      white-space: nowrap;
      overflow: hidden;
    }
    .lycia-preview-${scopeId} .Label.dynamic-label {
      color: #0000cc;
      font-weight: bold;
    }
    /* TextFields - Lycia default style */
    .lycia-preview-${scopeId} .TextField {
      background: transparent;
    }
    .lycia-preview-${scopeId} .TextField-input {
      background-color: #fff;
      border: 1px solid #7f9db9;
      padding: 1px 2px;
      font-family: Arial, sans-serif;
      font-size: 10px;
      color: #000;
      box-sizing: border-box;
      width: 100%;
      height: 100%;
    }
    .lycia-preview-${scopeId} .TextField.noentry .TextField-input,
    .lycia-preview-${scopeId} .TextField-input.noentry {
      background-color: #f0f0f0;
      color: #666;
    }
    /* Separators - Lycia default */
    .lycia-preview-${scopeId} .Separator {
      background-color: #808080;
    }
    .lycia-preview-${scopeId} .Separator.horizontal {
      height: 1px !important;
    }
    .lycia-preview-${scopeId} .Separator.vertical {
      width: 1px !important;
    }
    /* Buttons - Lycia default */
    .lycia-preview-${scopeId} .Button {
      background-color: #e0e0e0;
      color: #000;
      border: 1px solid #7f9db9;
      font-size: 10px;
      cursor: pointer;
    }
    .lycia-preview-${scopeId} .ComboBox-select {
      background-color: #fff;
      border: 1px solid #ced4da;
      border-radius: 3px;
      padding: 4px 8px;
      font-size: 12px;
    }
    .lycia-preview-${scopeId} .CheckBox {
      display: flex;
      align-items: center;
      gap: 6px;
    }
  `;

  useEffect(() => {
    if (!captureHtml) return;
    const html = previewRef.current?.outerHTML || "";
    onHtmlCapture?.(html);
  }, [
    captureHtml,
    formData,
    cssContent,
    showShell,
    showGrid,
    selectedComponent,
    scale,
    onHtmlCapture,
  ]);

  if (!formData || !formData.rootContainer) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        <p>No form data to display</p>
      </div>
    );
  }

  const formWidth = formData.width * CHAR_WIDTH * scale;
  const formHeight = formData.height * CHAR_HEIGHT * scale;

  const formSurface = (
    <div
      className="lycia-form-container relative border rounded shadow-sm mx-auto"
      style={{
        width: formWidth,
        minHeight: formHeight,
        transform: `scale(${scale})`,
        transformOrigin: "top left",
      }}
    >
      {/* Grid overlay */}
      {showGrid && (
        <div
          className="absolute inset-0 pointer-events-none opacity-10"
          style={{
            backgroundImage: `
              linear-gradient(to right, currentColor 1px, transparent 1px),
              linear-gradient(to bottom, currentColor 1px, transparent 1px)
            `,
            backgroundSize: `${CHAR_WIDTH}px ${CHAR_HEIGHT}px`,
          }}
        />
      )}

      {/* Render components */}
      <LyciaComponentRenderer
        component={formData.rootContainer}
        selectedComponent={selectedComponent}
        onSelectComponent={onSelectComponent}
      />
    </div>
  );

  return (
    <div className="relative overflow-auto p-4 bg-muted/30">
      <div ref={previewRef} className={cn(`lycia-preview-${scopeId}`)}>
        {/* Inject default styles */}
        <style dangerouslySetInnerHTML={{ __html: defaultStyles }} />

        {/* Inject user's scoped CSS (will override defaults) */}
        {scopedCss && (
          <style dangerouslySetInnerHTML={{ __html: scopedCss }} />
        )}

        <div
          className={cn(
            "lycia-preview-root",
            "body",
            "qx-application qx-informix4gl"
          )}
        >
          {showShell ? (
            <div className="qx-vdom">
              <div className="qx-aum-window qx-c-classic">
                <div id="qx-main-layout" className="qx-layout">
                  <header>
                    <span>Lycia Preview</span>
                    <div
                      className="qx-aum-menu-item md-button"
                      data-has-text
                      data-has-image
                    >
                      Menu
                    </div>
                    <div
                      className="qx-aum-toolbar-button md-button"
                      data-has-text
                      data-has-image
                    >
                      Toolbar
                    </div>
                  </header>
                  <div className="md-toolbars-container">
                    <div>Toolbar</div>
                  </div>
                  <div className="qx-aum">{formSurface}</div>
                </div>
              </div>
            </div>
          ) : (
            formSurface
          )}
        </div>
      </div>
    </div>
  );
}

interface LyciaComponentRendererProps {
  component: LyciaComponent;
  selectedComponent?: string | null;
  onSelectComponent?: (identifier: string | null) => void;
}

function LyciaComponentRenderer({
  component,
  selectedComponent,
  onSelectComponent,
}: LyciaComponentRendererProps) {
  const isSelected = selectedComponent === component.identifier;

  const identifierClass = component.identifier
    ? `qx-identifier-${component.identifier}`
    : "";

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSelectComponent?.(component.identifier);
  };

  // Calculate position and size
  const style: React.CSSProperties = {
    position: "absolute",
    left: component.x * CHAR_WIDTH,
    top: component.y * CHAR_HEIGHT,
    width: component.width * CHAR_WIDTH,
    height: component.height * CHAR_HEIGHT,
  };

  // Build CSS class names for this component
  const componentClass = component.type;

  // Render based on component type
  switch (component.type) {
    case "CoordPanel":
    case "GridPanel":
      return (
        <div
          id={component.identifier}
          className={cn(componentClass, "relative", identifierClass)}
          style={{
            width: component.width * CHAR_WIDTH,
            height: component.height * CHAR_HEIGHT,
          }}
          onClick={() => onSelectComponent?.(null)}
        >
          {component.children?.map((child, index) => (
            <LyciaComponentRenderer
              key={`${child.identifier || 'comp'}-${index}`}
              component={child}
              selectedComponent={selectedComponent}
              onSelectComponent={onSelectComponent}
            />
          ))}
        </div>
      );

    case "Label":
      return (
        <div
          id={component.identifier}
          data-identifier={component.identifier}
          data-isdynamic={component.isDynamic ? "true" : "false"}
          className={cn(
            componentClass,
            "Label",
            "flex items-center text-xs cursor-pointer transition-colors",
            isSelected && "ring-2 ring-primary ring-offset-1",
            component.isDynamic && "dynamic-label",
            identifierClass
          )}
          style={style}
          onClick={handleClick}
          title={`Label: ${component.identifier}`}
        >
          <span className="label-text truncate px-0.5">{component.text || ""}</span>
        </div>
      );

    case "TextField":
      return (
        <div
          id={component.identifier}
          data-identifier={component.identifier}
          data-noentry={component.noEntry ? "true" : "false"}
          data-tocase={component.toCase || ""}
          data-fieldtable={component.fieldTable || ""}
          data-has-trailing-button="false"
          className={cn(
            componentClass,
            "TextField",
            "md-tf md-tf-short",
            "flex items-center cursor-pointer transition-colors",
            isSelected && "ring-2 ring-primary ring-offset-1",
            component.noEntry && "noentry",
            identifierClass
          )}
          style={style}
          onClick={handleClick}
          title={`Field: ${component.identifier}\nTable: ${component.fieldTable || "formonly"}\nType: ${component.dataType || "Char"}`}
        >
          <div className="md-text-container w-full h-full">
            <input
              type="text"
              data-noentry={component.noEntry ? "true" : "false"}
              className={cn(
                "TextField-input md-input w-full h-full px-1 text-xs border pointer-events-none",
                component.toCase === "Up" && "uppercase",
                component.noEntry && "noentry"
              )}
              placeholder={component.identifier}
              disabled
              readOnly
            />
          </div>
        </div>
      );

    case "Separator":
      const isVertical = component.separatorType === "Vertical";
      return (
        <div
          id={component.identifier}
          data-identifier={component.identifier}
          data-separatortype={component.separatorType || "Horizontal"}
          className={cn(
            componentClass,
            "Separator",
            "cursor-pointer",
            isVertical ? "vertical" : "horizontal",
            isSelected && "ring-2 ring-primary",
            identifierClass
          )}
          style={{
            ...style,
            width: isVertical ? 2 : component.width * CHAR_WIDTH,
            height: isVertical ? component.height * CHAR_HEIGHT : 2,
            backgroundColor: "#ccc",
          }}
          onClick={handleClick}
          title={`Separator: ${component.identifier}`}
        />
      );

    case "Button":
      return (
        <button
          id={component.identifier}
          className={cn(
            componentClass,
            "Button",
            "px-2 py-0.5 text-xs border rounded hover:opacity-80 cursor-pointer",
            isSelected && "ring-2 ring-primary ring-offset-1",
            identifierClass,
            "qx-aum-button"
          )}
          style={style}
          onClick={handleClick}
          title={`Button: ${component.identifier}`}
        >
          {component.text || component.identifier}
        </button>
      );

    case "CheckBox":
      return (
        <div
          id={component.identifier}
          className={cn(
            componentClass,
            "CheckBox",
            "flex items-center gap-1 text-xs cursor-pointer",
            isSelected && "ring-2 ring-primary ring-offset-1",
            identifierClass,
            "qx-bool-widget"
          )}
          style={style}
          onClick={handleClick}
          title={`CheckBox: ${component.identifier}`}
        >
          <input type="checkbox" className="CheckBox-input" disabled />
          <span>{component.text || component.identifier}</span>
        </div>
      );

    case "ComboBox":
      return (
        <div
          id={component.identifier}
          className={cn(
            componentClass,
            "ComboBox",
            "cursor-pointer",
            isSelected && "ring-2 ring-primary ring-offset-1",
            identifierClass
          )}
          style={style}
          onClick={handleClick}
          title={`ComboBox: ${component.identifier}`}
        >
          <select
            className="ComboBox-select w-full h-full px-1 text-xs border"
            disabled
          >
            <option>{component.identifier}</option>
          </select>
        </div>
      );

    default:
      // Unknown component type - render as a box
      return (
        <div
          id={component.identifier}
          className={cn(
            componentClass,
            "border border-dashed border-gray-400 bg-gray-50 flex items-center justify-center text-xs text-gray-500 cursor-pointer",
            isSelected && "ring-2 ring-primary ring-offset-1",
            identifierClass
          )}
          style={style}
          onClick={handleClick}
          title={`${component.type}: ${component.identifier}`}
        >
          {component.type}
        </div>
      );
  }
}

// Component info panel
interface ComponentInfoProps {
  component: LyciaComponent | null;
}

export function LyciaComponentInfo({ component }: ComponentInfoProps) {
  if (!component) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Click on a component to see its properties
      </div>
    );
  }

  return (
    <div className="p-4 space-y-3">
      <div>
        <h3 className="font-semibold text-sm">Component Info</h3>
        <p className="text-xs text-muted-foreground">{component.type}</p>
      </div>

      <div className="space-y-2 text-xs">
        <div className="grid grid-cols-2 gap-1">
          <span className="text-muted-foreground">Identifier:</span>
          <span className="font-mono">{component.identifier}</span>
        </div>

        <div className="grid grid-cols-2 gap-1">
          <span className="text-muted-foreground">Position:</span>
          <span className="font-mono">
            ({component.x}, {component.y})
          </span>
        </div>

        <div className="grid grid-cols-2 gap-1">
          <span className="text-muted-foreground">Size:</span>
          <span className="font-mono">
            {component.width} x {component.height}
          </span>
        </div>

        {component.text && (
          <div className="grid grid-cols-2 gap-1">
            <span className="text-muted-foreground">Text:</span>
            <span className="font-mono">{component.text}</span>
          </div>
        )}

        {component.fieldTable && (
          <div className="grid grid-cols-2 gap-1">
            <span className="text-muted-foreground">Field Table:</span>
            <span className="font-mono">{component.fieldTable}</span>
          </div>
        )}

        {component.dataType && (
          <div className="grid grid-cols-2 gap-1">
            <span className="text-muted-foreground">Data Type:</span>
            <span className="font-mono">{component.dataType}</span>
          </div>
        )}

        {component.noEntry && (
          <div className="grid grid-cols-2 gap-1">
            <span className="text-muted-foreground">No Entry:</span>
            <span className="font-mono text-orange-600">Yes</span>
          </div>
        )}

        {component.toCase && (
          <div className="grid grid-cols-2 gap-1">
            <span className="text-muted-foreground">To Case:</span>
            <span className="font-mono">{component.toCase}</span>
          </div>
        )}
      </div>
    </div>
  );
}
