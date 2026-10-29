import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MarketSummary } from '@/shared/models/market.models';
import { API_BASE_URL } from '@/core/config/api.config';

@Component({ selector: 'ki-dashboard', standalone: false, templateUrl: './dashboard.component.html' })
export class DashboardComponent implements OnInit {
  summary: MarketSummary | null = null; loading = true; error = '';
  constructor(private readonly http: HttpClient) {}
  ngOnInit(): void { this.http.get<MarketSummary>(`${API_BASE_URL}/analytics/dashboard`).subscribe({ next: value => { this.summary = value; this.loading = false; }, error: () => { this.error = 'No se pudo cargar el dashboard'; this.loading = false; } }); }
}

