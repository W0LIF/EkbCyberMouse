import { type FormEvent, useState } from "react";
import { AlertCircle, ArrowRight, Check, Eye, EyeOff, Info, Lock, User } from "lucide-react";
import { Button } from "../shared/ui/Button";
import { Tooltip } from "../shared/ui/Tooltip";

interface LoginPageProps {
  onLogin: () => void;
}

export function LoginPage({ onLogin }: LoginPageProps) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState(false);
  const [leaving, setLeaving] = useState(false);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (login === "admin" && password === "admin") {
      setError(false);
      setLeaving(true);
      setTimeout(onLogin, 200);
    } else {
      setError(true);
    }
  }

  return (
    <main className={`login-page ${leaving ? "fade-out" : ""}`}>
      <section className="login-brand">
        <div className="road-grid" />
        <div className="brand-center">
          <img src="/rostel.png" alt="Ростелеком" className="brand-logo" />
          <span className="brand-name">Ростелеком</span>
          <h1>
            Умная диспетчеризация
            <br />
            выездных бригад
          </h1>
          <span className="brand-line" />
          <p>Екатеринбург · 2026</p>
        </div>
        <div className="brand-foot">ПАО «Ростелеком» · Сервисный центр</div>
      </section>
      <section className="login-surface">
        <form className={`login-card ${error ? "shake" : ""}`} onSubmit={submit}>
          <div className="login-title">
            <div>
              <span className="eyebrow">СИСТЕМА УПРАВЛЕНИЯ</span>
              <h2>Вход в систему</h2>
            </div>
            <Tooltip text="Доступ выдаётся администратором СЦ. При проблемах — тикет в IT-поддержку.">
              <Info size={18} />
            </Tooltip>
          </div>
          <p className="muted">Введите учётные данные администратора</p>
          <label>Логин</label>
          <div className={`field ${error ? "field-error" : ""}`}>
            <User size={18} />
            <input
              value={login}
              onChange={(e) => {
                setLogin(e.target.value);
                setError(false);
              }}
              placeholder="admin"
              autoFocus
            />
          </div>
          <label>Пароль</label>
          <div className={`field ${error ? "field-error" : ""}`}>
            <Lock size={18} />
            <input
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setError(false);
              }}
              type={show ? "text" : "password"}
              placeholder="••••••"
            />
            <button type="button" onClick={() => setShow(!show)} aria-label="Показать пароль">
              {show ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
          {error && (
            <div className="error-text">
              <AlertCircle size={14} /> Неверный логин или пароль
            </div>
          )}
          <div className="login-options">
            <label className="check">
              <input type="checkbox" />
              <span>
                <Check size={12} />
              </span>
              Запомнить меня
            </label>
            <a>Забыли пароль?</a>
          </div>
          <Button type="submit">
            Войти <ArrowRight size={17} />
          </Button>
          <div className="demo">login: admin · password: admin</div>
          <div className="secure-note">
            <Lock size={12} /> Доступ только для сотрудников сервисного центра
          </div>
        </form>
      </section>
    </main>
  );
}
