import { useState } from "react";
import { ArrowRight } from "lucide-react";
import { Button } from "../../shared/ui/Button";

interface OnboardingProps {
  finish: () => void;
}

const steps = [
  ["Добро пожаловать", "Здесь собрана оперативная картина по всем выездным бригадам."],
  ["Навигация", "Переключайтесь между картой, планом, рисками и ПГП."],
  ["Карта маршрутов", "Следите за визитами, рисками и текущим положением бригад."],
  ["План и загрузка", "Откройте Gantt, чтобы увидеть загрузку в течение дня."],
  ["Всё готово", "Подсказки доступны в любое время по кнопке «?» в шапке."],
];

export function Onboarding({ finish }: OnboardingProps) {
  const [step, setStep] = useState(0);

  return (
    <div className="tour">
      <div className="tour-card">
        <span>ШАГ {step + 1} ИЗ 5</span>
        <h2>{steps[step][0]}</h2>
        <p>{steps[step][1]}</p>
        <div>
          <button onClick={finish}>Пропустить</button>
          <Button onClick={() => (step === 4 ? finish() : setStep(step + 1))}>
            {step === 4 ? "Понятно" : "Далее"}
            <ArrowRight size={15} />
          </Button>
        </div>
      </div>
    </div>
  );
}
