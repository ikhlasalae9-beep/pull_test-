'use client';

import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, Check } from 'lucide-react';
import { compatibleNeighborhood, neighborhoodForApi } from '@/lib/estimation/locations';
import locations from '@/models/locations_v1.json';
import { ESTIMATOR_STEPS } from '@/config/estimator.config';
import { EstimatorFormData, EstimationStatus } from '@/types/estimator';
import { PredictResponse } from '@/lib/api/types';
import { predictProperty } from '@/lib/api/client';
import { isRTL } from '@/lib/i18n/config';
import { Button } from '@/components/common/Button';

import { Step1Location } from './Step1Location';
import { Step2PropertyType } from './Step2PropertyType';
import { Step3Features } from './Step3Features';
import { Step4Review } from './Step4Review';
import { Step5Result } from './Step5Result';

interface EstimatorShellProps {
  locale: string;
  dict: any;
}

export function EstimatorShell({ locale, dict }: EstimatorShellProps) {
  const searchParams = useSearchParams();
  const rtl = isRTL(locale);
  const ArrowIcon = rtl ? ArrowLeft : ArrowRight;
  const BackArrowIcon = rtl ? ArrowRight : ArrowLeft;

  // Initial form values
  const [formData, setFormData] = useState<EstimatorFormData>({
    ville: 'Casablanca',
    quartier: '',
    parking: 'unknown', balcony: 'unknown', sea_view: 'unknown', furnished_status: 'unknown',
    type_bien: 'appartement',
    surface: 90,
    chambres: 2,
    salles_bain: 1,
  });

  // Prefill from URL search params (e.g. from Hero or Location Explorer)
  useEffect(() => {
    const villeParam = searchParams.get('ville');
    const surfaceParam = searchParams.get('surface');

    setFormData((prev) => ({
      ...prev,
      ville: villeParam && villeParam in locations ? villeParam : prev.ville,
      quartier: compatibleNeighborhood(villeParam && villeParam in locations ? villeParam : prev.ville, prev.quartier),
      surface: surfaceParam ? Number(surfaceParam) : prev.surface,
    }));
  }, [searchParams]);

  const [currentStep, setCurrentStep] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [error, setError] = useState<string | undefined>();
  const [prediction, setPrediction] = useState<PredictResponse | null>(null);

  const updateForm = (key: string, value: any) => {
    setFormData((prev) => ({ ...prev, [key]: value,
      quartier: key === 'ville' ? compatibleNeighborhood(value, prev.quartier)
        : key === 'quartier' ? compatibleNeighborhood(prev.ville, value) : prev.quartier,
    }));
  };

  const handleNext = () => {
    // Basic step validation
    if (currentStep === 1 && !formData.ville) return;
    if (currentStep === 3 && (!formData.surface || formData.surface <= 0)) return;

    if (currentStep < 4) {
      setCurrentStep((prev) => prev + 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else if (currentStep === 4) {
      handleFinalSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep((prev) => prev - 1);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleFinalSubmit = async () => {
    setCurrentStep(5);
    setIsSubmitting(true);
    setIsOffline(false);
    setError(undefined);
    setPrediction(null);

    const res = await predictProperty({
      city: formData.ville,
      region: (locations as Record<string, string>)[formData.ville],
      neighborhood: neighborhoodForApi(formData.ville, formData.quartier),
      property_type: formData.type_bien,
      surface_m2: Number(formData.surface),
      bedrooms: String(formData.chambres) === '' ? null : Number(formData.chambres),
      bathrooms: String(formData.salles_bain) === '' ? null : Number(formData.salles_bain),
      parking: formData.parking,
      balcony: formData.balcony,
      sea_view: formData.sea_view,
      furnished_status: formData.furnished_status,
    });

    setIsSubmitting(false);

    if (res.isOffline) {
      setIsOffline(true);
      setError(res.error);
    } else if (res.error) {
      setError(res.error);
    } else if (res.data) {
      setPrediction(res.data);
    }
  };

  const handleReset = () => {
    setPrediction(null);
    setIsOffline(false);
    setError(undefined);
    setCurrentStep(1);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const currentStepMeta = ESTIMATOR_STEPS.find((s) => s.step === currentStep);

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Step Progress Indicator */}
      <div className="mb-10 sm:mb-14">
        {/* Step bars */}
        <div className="flex items-center justify-between gap-2 sm:gap-3 mb-4">
          {ESTIMATOR_STEPS.map((s) => {
            const isDone = s.step < currentStep;
            const isCurrent = s.step === currentStep;

            return (
              <div key={s.step} className="flex-1">
                <div
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    isDone
                      ? 'bg-emerald-500'
                      : isCurrent
                      ? 'bg-brand-blue'
                      : 'bg-slate-200 dark:bg-slate-800'
                  }`}
                />
              </div>
            );
          })}
        </div>

        {/* Current Step Title & Subtitle */}
        {currentStepMeta && (
          <div className="text-center">
            <span className="text-xs font-bold uppercase tracking-wider text-brand-blue dark:text-blue-400 block mb-1">
              Étape {currentStep} sur 5
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white">
              {locale === 'ar' ? currentStepMeta.titleAr : currentStepMeta.titleFr}
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1">
              {locale === 'ar' ? currentStepMeta.subtitleAr : currentStepMeta.subtitleFr}
            </p>
          </div>
        )}
      </div>

      {/* Step Content Container */}
      <div className="bg-white dark:bg-brand-navy-surface border border-slate-200/90 dark:border-white/10 rounded-3xl p-6 sm:p-10 shadow-xl shadow-slate-900/5 dark:shadow-black/40 mb-8 transition-colors">
        {currentStep === 1 && (
          <Step1Location
            formData={formData}
            updateForm={updateForm}
            locale={locale}
            dict={dict}
          />
        )}

        {currentStep === 2 && (
          <Step2PropertyType
            formData={formData}
            updateForm={updateForm}
            locale={locale}
            dict={dict}
          />
        )}

        {currentStep === 3 && (
          <Step3Features
            formData={formData}
            updateForm={updateForm}
            locale={locale}
            dict={dict}
          />
        )}

        {currentStep === 4 && (
          <Step4Review
            formData={formData}
            goToStep={(step) => setCurrentStep(step)}
            locale={locale}
            dict={dict}
          />
        )}

        {currentStep === 5 && (
          <Step5Result
            prediction={prediction}
            isSubmitting={isSubmitting}
            isOffline={isOffline}
            error={error}
            formData={formData}
            onRetry={handleFinalSubmit}
            onReset={handleReset}
            locale={locale}
            dict={dict}
          />
        )}
      </div>

      {/* Step Navigation Controls (Steps 1-4) */}
      {currentStep < 5 && (
        <div className="flex items-center justify-between gap-4">
          {currentStep > 1 ? (
            <Button
              variant="outline"
              size="md"
              onClick={handleBack}
              icon={<BackArrowIcon className="w-4 h-4" />}
              iconPosition="start"
            >
              {dict.common.back}
            </Button>
          ) : (
            <div />
          )}

          <Button
            variant="primary"
            size="md"
            onClick={handleNext}
            icon={<ArrowIcon className="w-4 h-4" />}
          >
            {currentStep === 4 ? dict.common.finish : dict.common.continue}
          </Button>
        </div>
      )}
    </div>
  );
}
