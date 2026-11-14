import { useState } from "react";
import {
  Bell,
  Check,
  ChevronRight,
  FileText,
  Info,
  Layers3,
  Lock,
  Settings,
  SlidersHorizontal,
} from "lucide-react";
import { Button } from "../shared/ui/Button";
import { Toggle } from "../shared/ui/Toggle";
import { Tooltip } from "../shared/ui/Tooltip";
import { PageIntro } from "../shared/ui/PageIntro";
import { useToast } from "../features/toast/ToastProvider";

export default function SettingsPage() {
  const [tab, setTab] = useState("Оптимизация");
  const [toggles, setToggles] = useState([true, true, false, true]);
  const [weight, setWeight] = useState(65);
  const { toast } = useToast();

  function flip(index: number) {
    setToggles((current) => current.map((value, i) => (i === index ? !value : value)));
  }

  return (
    <div className="screen">
      <PageIntro
        eyebrow="КОНФИГУРАЦИЯ СИСТЕМЫ"
        title="Настройки"
        subtitle="Параметры планирования, уведомлений и интеграций"
        actions={
          <Button icon={<Check size={17} />} onClick={() => toast("Настройки сохранены")}>
            Сохранить изменения
          </Button>
        }
      />
      <div className="settings-layout">
        <aside className="settings-nav card">
          {["Оптимизация", "Уведомления", "Интеграции", "Роли и доступ", "Справочники"].map(
            (item, index) => {
              const Icon = [SlidersHorizontal, Bell, Layers3, Lock, FileText][index];
              return (
                <button
                  className={tab === item ? "active" : ""}
                  onClick={() => setTab(item)}
                  key={item}
                >
                  <Icon size={17} />
                  {item}
                  <ChevronRight size={14} />
                </button>
              );
            },
          )}
        </aside>
        <section className="settings-panel card">
          <div className="settings-title">
            <div>
              <h2>{tab}</h2>
              <p>
                {tab === "Оптимизация"
                  ? "Настройте приоритеты алгоритма распределения нарядов."
                  : "Управляйте параметрами раздела и доступностью функций."}
              </p>
            </div>
            <Tooltip text="Изменения применяются при следующем пересчёте плана">
              <Info size={17} />
            </Tooltip>
          </div>
          {tab === "Оптимизация" ? (
            <>
              <div className="setting-group">
                <h3>Целевая функция</h3>
                <div className="range-setting">
                  <div>
                    <span>Приоритет соблюдения слота</span>
                    <b>{weight}%</b>
                  </div>
                  <input
                    type="range"
                    min="20"
                    max="90"
                    value={weight}
                    onChange={(event) => setWeight(+event.target.value)}
                  />
                  <small>
                    Чем выше значение, тем чаще система выберет более длинный маршрут ради
                    соблюдения слота.
                  </small>
                </div>
                {[
                  [
                    "Учитывать текущие пробки",
                    "Данные Яндекс.Маршрутизации обновляются раз в 3 минуты",
                  ],
                  ["Балансировать загрузку", "Ограничивать отклонение загрузки сотрудников до 15%"],
                  ["Разрешить сверхурочную работу", "Не более 60 минут после завершения смены"],
                  ["Учитывать остатки АО", "Проверять оборудование в рюкзаке перед назначением"],
                ].map((item, index) => (
                  <div className="setting-row" key={item[0]}>
                    <div>
                      <b>{item[0]}</b>
                      <small>{item[1]}</small>
                    </div>
                    <Toggle active={toggles[index]} onClick={() => flip(index)} />
                  </div>
                ))}
              </div>
              <div className="setting-group">
                <h3>Ограничения планирования</h3>
                <div className="form-grid">
                  <label>
                    Максимальный пробег, км
                    <input defaultValue="120" />
                  </label>
                  <label>
                    Буфер между визитами, мин
                    <input defaultValue="15" />
                  </label>
                  <label>
                    Горизонт планирования
                    <select defaultValue="7">
                      <option value="7">7 дней</option>
                      <option value="14">14 дней</option>
                    </select>
                  </label>
                  <label>
                    Пересчёт плана
                    <select defaultValue="10">
                      <option value="10">Каждые 10 минут</option>
                      <option value="30">Каждые 30 минут</option>
                    </select>
                  </label>
                </div>
              </div>
            </>
          ) : (
            <div className="settings-placeholder">
              <span>{tab === "Уведомления" ? <Bell size={29} /> : <Settings size={29} />}</span>
              <h3>Настройки раздела «{tab}»</h3>
              <p>Основные параметры подключены и доступны администратору системы.</p>
              {["Критические события", "Ежедневный отчёт", "Журнал изменений"].map(
                (item, index) => (
                  <div className="setting-row" key={item}>
                    <div>
                      <b>{item}</b>
                      <small>Системная настройка № {index + 1}</small>
                    </div>
                    <Toggle active={toggles[index]} onClick={() => flip(index)} />
                  </div>
                ),
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
