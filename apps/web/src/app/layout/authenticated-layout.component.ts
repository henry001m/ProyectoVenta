import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { SessionService } from '@/core/auth/session.service';

@Component({ selector: 'ki-auth-layout', standalone: false, templateUrl: './authenticated-layout.component.html', styleUrls: ['./authenticated-layout.component.scss'] })
export class AuthenticatedLayoutComponent {
  constructor(private readonly session: SessionService, private readonly router: Router) {}
  logout(): void { this.session.clear(); void this.router.navigate(['/auth/login']); }
}

