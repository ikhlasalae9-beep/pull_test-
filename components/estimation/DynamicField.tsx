'use client';

import React from 'react';
import { EstimatorField } from '@/config/estimator.config';
import locations from '@/models/locations_v1.json';

interface DynamicFieldProps {
  field: EstimatorField;
  value: any;
  onChange: (value: any) => void;
  locale: string;
  dict: any;
}

export function DynamicField({ field, value, onChange, locale, dict }: DynamicFieldProps) {
  const label = locale === 'ar' ? field.labelAr : field.labelFr;
  const hint = locale === 'ar' ? field.hintAr : field.hintFr;
  const placeholder = locale === 'ar' ? field.placeholderAr : field.placeholderFr;

  // Number field
  if (field.type === 'number') {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor={field.id} className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            {label} {field.required && <span className="text-rose-500">*</span>}
          </label>
          {field.unit && (
            <span className="text-xs font-mono text-slate-400">{field.unit}</span>
          )}
        </div>

        <div className="relative">
          <input
            id={field.id}
            type="number"
            min={field.min}
            max={field.max}
            step={field.stepValue || 1}
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value === '' ? '' : Number(e.target.value))}
            placeholder={placeholder}
            className="w-full px-4 py-3 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-white/10 rounded-xl text-base font-semibold text-slate-900 dark:text-white focus:outline-none focus:border-brand-blue transition-colors"
          />
        </div>

        {hint && (
          <p className="text-xs text-slate-500 dark:text-slate-400">{hint}</p>
        )}
      </div>
    );
  }

  // Select field (e.g. Cities)
  if (field.type === 'select') {
    return (
      <div className="space-y-2">
        <label htmlFor={field.id} className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
          {label} {field.required && <span className="text-rose-500">*</span>}
        </label>

        <select
          id={field.id}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-4 py-3 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-white/10 rounded-xl text-base font-semibold text-slate-900 dark:text-white focus:outline-none focus:border-brand-blue cursor-pointer transition-colors"
        >
          {field.id === 'ville'
            ? Object.entries(locations).map(([city, region]) => (
                <option key={city} value={city}>{city} ({region})</option>
              ))
            : field.options?.map((opt) => (
                <option key={opt.value} value={opt.value} disabled={opt.disabled}>
                  {locale === 'ar' ? opt.labelAr : opt.labelFr}
                </option>
              ))}
        </select>

        {hint && (
          <p className="text-xs text-slate-500 dark:text-slate-400">{hint}</p>
        )}
      </div>
    );
  }

  // Text field (e.g. Quartier)
  if (field.type === 'text') {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor={field.id} className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            {label} {field.required && <span className="text-rose-500">*</span>}
          </label>
        </div>

        <input
          id={field.id}
          type="text"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full px-4 py-3 bg-white dark:bg-slate-800/80 border border-slate-200 dark:border-white/10 rounded-xl text-base text-slate-900 dark:text-white focus:outline-none focus:border-brand-blue transition-colors"
        />

        {hint && (
          <p className="text-xs text-slate-500 dark:text-slate-400">{hint}</p>
        )}
      </div>
    );
  }

  // Toggle field
  if (field.type === 'toggle') {
    const isChecked = Boolean(value);
    return (
      <div className="p-4 rounded-xl border border-slate-200 dark:border-white/10 bg-slate-50/50 dark:bg-slate-800/40 flex items-center justify-between gap-4">
        <div>
          <label className="text-sm font-bold text-slate-900 dark:text-white block">
            {label}
          </label>
          {hint && (
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{hint}</p>
          )}
        </div>

        <button
          type="button"
          onClick={() => onChange(isChecked ? 0 : 1)}
          className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
            isChecked ? 'bg-brand-blue' : 'bg-slate-300 dark:bg-slate-700'
          }`}
          role="switch"
          aria-checked={isChecked}
        >
          <span
            className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
              isChecked ? 'translate-x-5 rtl:-translate-x-5' : 'translate-x-0'
            }`}
          />
        </button>
      </div>
    );
  }

  // Radio cards
  if (field.type === 'radio' && field.options) {
    return (
      <div className="space-y-3">
        <label className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 block">
          {label}
        </label>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {field.options.map((opt) => {
            const isSelected = value === opt.value;
            const optLabel = locale === 'ar' ? opt.labelAr : opt.labelFr;
            const optDesc = locale === 'ar' ? opt.descriptionAr : opt.descriptionFr;

            return (
              <div
                key={opt.value}
                onClick={() => {
                  if (!opt.disabled) onChange(opt.value);
                }}
                className={`p-4 rounded-xl border transition-all ${
                  opt.disabled
                    ? 'opacity-45 bg-slate-100 dark:bg-slate-800/30 border-dashed border-slate-200 dark:border-slate-800 cursor-not-allowed'
                    : isSelected
                    ? 'bg-brand-blue/5 dark:bg-blue-500/10 border-brand-blue dark:border-blue-400 cursor-pointer shadow-sm'
                    : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-white/10 hover:border-slate-300 cursor-pointer'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {optLabel}
                  </span>
                  {opt.disabled ? (
                    <span className="text-[10px] font-semibold text-slate-400 uppercase">
                      {locale === 'ar' ? 'قيد التطوير' : 'À venir'}
                    </span>
                  ) : isSelected ? (
                    <span className="w-2.5 h-2.5 rounded-full bg-brand-blue" />
                  ) : null}
                </div>
                {optDesc && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    {optDesc}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return null;
}
