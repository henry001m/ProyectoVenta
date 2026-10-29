import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { AuthGuard } from '@/core/auth/auth.guard';
import { AuthenticatedLayoutComponent } from '@/layout/authenticated-layout.component';

const routes: Routes = [
  { path: 'auth', loadChildren: () => import('./features/auth/auth.module').then(m => m.AuthModule) },
  { path: '', component: AuthenticatedLayoutComponent, canActivate: [AuthGuard], children: [
    { path: 'dashboard', loadChildren: () => import('./features/dashboard/dashboard.module').then(m => m.DashboardModule) },
    { path: 'observations', loadChildren: () => import('./features/observations/observations.module').then(m => m.ObservationsModule) },
    { path: 'sources', loadChildren: () => import('./features/sources/sources.module').then(m => m.SourcesModule) },
    { path: '', pathMatch: 'full', redirectTo: 'dashboard' },
  ] },
  { path: '**', redirectTo: 'auth' },
];

@NgModule({ imports: [RouterModule.forRoot(routes)], exports: [RouterModule] })
export class AppRoutingModule {}

