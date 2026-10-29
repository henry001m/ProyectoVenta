import { createFeatureSelector, createSelector } from '@ngrx/store';
import { SessionState } from './session.reducer';

export const selectSession = createFeatureSelector<SessionState>('session');
export const selectRole = createSelector(selectSession, state => state.role);

