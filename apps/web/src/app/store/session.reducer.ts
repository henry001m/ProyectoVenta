import { createReducer, on } from '@ngrx/store';
import { sessionCleared, sessionLoaded } from './session.actions';

export interface SessionState { userId: number | null; role: string | null; }
export const initialSessionState: SessionState = { userId: null, role: null };
export const sessionReducer = createReducer(initialSessionState, on(sessionLoaded, (_, payload) => ({ userId: payload.userId, role: payload.role })), on(sessionCleared, () => initialSessionState));

