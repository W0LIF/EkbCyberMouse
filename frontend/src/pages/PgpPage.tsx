import { RefreshCw, Zap } from "lucide-react";
import { useDispatchData } from "../features/dispatch/DispatchDataContext";
import { Button } from "../shared/ui/Button";
import { Status } from "../shared/ui/Status";
import { PageIntro } from "../shared/ui/PageIntro";

export default function PgpPage() {
  const { plan, orders, loading, error, refresh } = useDispatchData();
  const orderById = new Map(orders.map((order) => [order.order_id, order]));
  const groups = plan?.pgp_groups ?? [];

  return (
    <div className="screen">
      <PageIntro
        eyebrow={`${groups.length} ГРУППОВЫХ СОБЫТИЙ`}
        eyebrowTone="purple"
        title="Проактивные групповые повреждения"
        subtitle="Группы и наряды из текущего диспетчерского плана"
        actions={
          <Button
            variant="secondary"
            icon={<RefreshCw size={16} />}
            disabled={loading}
            onClick={() => void refresh()}
          >
            Обновить
          </Button>
        }
      />
      {error && <div className="card" role="alert">{error}</div>}
      {loading && <div className="card" role="status">Загружаем группы…</div>}
      <div className="pgp-grid">
        {groups.map((group) => (
          <article className="pgp-card card" key={group.group_id}>
            <div className="pgp-accent" />
            <div className="pgp-info">
              <div className="pgp-title">
                <span>
                  <Zap size={18} />
                </span>
                <div>
                  <h2>Узел {group.access_node_id}</h2>
                  <p>{group.comment ?? `${group.order_ids.length} нарядов в группе`}</p>
                </div>
                <Status>ПГП</Status>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Адрес</th>
                    <th>Слот</th>
                  </tr>
                </thead>
                <tbody>
                  {group.order_ids.map((orderId) => {
                    const order = orderById.get(orderId);
                    return (
                      <tr key={orderId}>
                        <td><code>{orderId}</code></td>
                        <td>{order?.address ?? "Адрес недоступен"}</td>
                        <td>
                          {order
                            ? `${order.slot.start.slice(11, 16)}–${order.slot.end.slice(11, 16)}`
                            : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              <small>Обнаружено: {new Date(group.detected_at).toLocaleString("ru-RU")}</small>
            </div>
            <div className="mini-map">
              <div className="mini-roads" />
              <span className="radius" />
              <span className="node">
                <Zap size={16} />
              </span>
              <b>{group.access_node_id}</b>
              <small>{group.order_ids.length} нарядов · передача в СЦ</small>
            </div>
          </article>
        ))}
        {!loading && groups.length === 0 && (
          <div className="card">В текущем плане нет групповых повреждений.</div>
        )}
      </div>
    </div>
  );
}
