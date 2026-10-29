import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { SessionService } from '@/core/auth/session.service';

@Component({ selector: 'ki-login', standalone: false, templateUrl: './login.component.html', styleUrls: ['./login.component.scss'] })
export class LoginComponent {
  email = 'demo@kicks.local'; password = 'password123'; error = '';
  constructor(private readonly session: SessionService, private readonly router: Router) {}
  login(): void { this.session.setSession({ accessToken: 'local-demo-token', refreshToken: 'local-demo-refresh' }); void this.router.navigate(['/dashboard']); }
}

