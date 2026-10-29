import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { DashboardComponent } from './dashboard.component';
import { DashboardModule } from './dashboard.module';
import { RouterTestingModule } from '@angular/router/testing';

describe('DashboardComponent', () => {
  it('creates', () => { TestBed.configureTestingModule({ imports: [HttpClientTestingModule, DashboardModule, RouterTestingModule] }); expect(TestBed.createComponent(DashboardComponent).componentInstance).toBeTruthy(); });
});

