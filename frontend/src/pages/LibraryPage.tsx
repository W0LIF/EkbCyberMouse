import { AlertCircle, Bell, CircleHelp, HelpCircle, Info, Search } from "lucide-react";
import { Button } from "../shared/ui/Button";
import { Status } from "../shared/ui/Status";
import { Tooltip } from "../shared/ui/Tooltip";
import { Chips } from "../shared/ui/Chips";
import { PageIntro } from "../shared/ui/PageIntro";

export default function LibraryPage() {
  return (
    <div className="screen">
      <PageIntro
        eyebrow="DESIGN SYSTEM 1.0"
        title="Компонентная библиотека"
        subtitle="Базовые элементы интерфейса и состояния"
      />
      <div className="library-grid">
        <section className="card">
          <h2>Кнопки</h2>
          <div className="component-row">
            <Button>Основная</Button>
            <Button variant="secondary">Вторичная</Button>
            <Button variant="purple">Акцент</Button>
            <Button disabled>Недоступна</Button>
          </div>
        </section>
        <section className="card">
          <h2>Статусы</h2>
          <div className="component-row">
            {["Запланирован", "В работе", "Выполнен", "Риск", "Не распределён", "ПГП", "Отменён"].map(
              (s) => (
                <Status key={s}>{s}</Status>
              ),
            )}
          </div>
        </section>
        <section className="card">
          <h2>Поля и чипы</h2>
          <div className="component-row vertical">
            <div className="field">
              <Search size={17} />
              <input placeholder="Обычное состояние" />
            </div>
            <div className="field field-error">
              <AlertCircle size={17} />
              <input placeholder="Состояние ошибки" />
            </div>
            <Chips items={["Active", "Default"]} selected="Active" />
          </div>
        </section>
        <section className="card">
          <h2>Подсказки и иконки</h2>
          <div className="component-row icons">
            <Tooltip text="Подсказка сверху">
              <Info size={16} />
            </Tooltip>
            <HelpCircle size={20} />
            <Bell size={24} />
            <Tooltip text="Действие или дополнительная информация">
              <button className="icon-button">
                <CircleHelp size={20} />
              </button>
            </Tooltip>
          </div>
        </section>
      </div>
    </div>
  );
}
