import { useState } from "react";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Filter,
  MoreHorizontal,
  Plus,
  Search,
  SlidersHorizontal,
  ToolCase,
} from "lucide-react";
import type { ModalType } from "../shared/types/domain";
import { orders } from "../shared/mock/orders";
import { Button } from "../shared/ui/Button";
import { Status } from "../shared/ui/Status";
import { PageIntro } from "../shared/ui/PageIntro";

interface OrdersPageProps {
  setModal: (m: ModalType) => void;
}

export default function OrdersPage({ setModal }: OrdersPageProps) {
  const [selected, setSelected] = useState<string[]>([]);

  return (
    <div className="screen">
      <PageIntro
        eyebrow="127 НАРЯДОВ СЕГОДНЯ"
        title="Наряды"
        subtitle="Единый реестр работ сервисного центра"
        actions={
          <Button icon={<Plus size={17} />}>Новый наряд</Button>
        }
      />
      <div className="table-filters card">
        <div className="search-small">
          <Search size={16} />
          <input placeholder="ID, адрес, сотрудник…" />
        </div>
        <button>
          <CalendarDays size={16} />
          14 ноября
        </button>
        <button>
          <Filter size={16} />
          Статус
        </button>
        <button>Профиль</button>
        <button>
          <SlidersHorizontal size={16} />
          Сортировка
        </button>
      </div>
      {selected.length > 0 && (
        <div className="bulk">
          <b>Выбрано: {selected.length}</b>
          <Button variant="secondary">Переназначить</Button>
          <Button variant="ghost">Экспорт CSV</Button>
          <Button variant="danger">Отменить</Button>
        </div>
      )}
      <div className="orders-table card">
        <table>
          <thead>
            <tr>
              <th>
                <input type="checkbox" />
              </th>
              <th>ID</th>
              <th>Тип работ</th>
              <th>Адрес</th>
              <th>Слот</th>
              <th>Сотрудник</th>
              <th>СЦ</th>
              <th>Статус</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} onClick={() => setModal("order")}>
                <td onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selected.includes(o.id)}
                    onChange={() =>
                      setSelected((s) =>
                        s.includes(o.id) ? s.filter((x) => x !== o.id) : [...s, o.id],
                      )
                    }
                  />
                </td>
                <td>
                  <code>{o.id}</code>
                </td>
                <td>
                  <span className="work-type">
                    <ToolCase size={15} />
                    {o.type}
                  </span>
                </td>
                <td>{o.address}</td>
                <td>{o.slot}</td>
                <td>{o.person}</td>
                <td>{o.center}</td>
                <td>
                  <Status>{o.status}</Status>
                </td>
                <td>
                  <MoreHorizontal size={17} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="pagination">
          <span>1–6 из 127</span>
          <span>50 строк на странице</span>
          <div>
            <button>
              <ChevronLeft size={16} />
            </button>
            <button className="current">1</button>
            <button>2</button>
            <button>3</button>
            <button>
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
