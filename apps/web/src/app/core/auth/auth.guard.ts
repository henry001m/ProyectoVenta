import { Injectable } from '@angular/core';
import { CanActivate, Router, UrlTree } from '@angular/router';
import { SessionService } from './session.service';

@Injectable({ providedIn: 'root' })
export class AuthGuard implements CanActivate {
  constructor(private readonly session: SessionService, private readonly router: Router) {}
  canActivate(): boolean | UrlTree { return this.session.isAuthenticated ? true : this.router.parseUrl('/auth'); }
}

