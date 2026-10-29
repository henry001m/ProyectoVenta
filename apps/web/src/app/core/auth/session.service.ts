import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface Session { accessToken: string; refreshToken: string; }

@Injectable({ providedIn: 'root' })
export class SessionService {
  private readonly subject = new BehaviorSubject<Session | null>(this.read());
  readonly session$: Observable<Session | null> = this.subject.asObservable();
  get token(): string | null { return this.subject.value?.accessToken ?? null; }
  get isAuthenticated(): boolean { return Boolean(this.token); }
  setSession(session: Session): void { localStorage.setItem('ki_session', JSON.stringify(session)); this.subject.next(session); }
  clear(): void { localStorage.removeItem('ki_session'); this.subject.next(null); }
  private read(): Session | null { try { const raw = localStorage.getItem('ki_session'); return raw ? JSON.parse(raw) as Session : null; } catch { return null; } }
}

