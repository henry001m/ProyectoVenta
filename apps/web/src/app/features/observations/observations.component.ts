import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observation } from '@/shared/models/market.models';
import { API_BASE_URL } from '@/core/config/api.config';

@Component({ selector: 'ki-observations', standalone: false, templateUrl: './observations.component.html' })
export class ObservationsComponent implements OnInit {
  items: Observation[] = []; rawText = ''; sourceUrl = ''; loading = false; error = '';
  constructor(private readonly http: HttpClient) {}
  ngOnInit(): void { this.load(); }
  load(): void { this.http.get<Observation[]>(`${API_BASE_URL}/observations`).subscribe({ next: items => this.items = items, error: () => this.error = 'No se pudieron cargar las observaciones' }); }
  create(): void { if (!this.rawText.trim()) return; this.loading = true; this.http.post<Observation>(`${API_BASE_URL}/sources/import`, { raw_text: this.rawText, source_url: this.sourceUrl, content_type: this.sourceUrl ? 'link' : 'text' }).subscribe({ next: item => { this.items = [item, ...this.items]; this.rawText = ''; this.sourceUrl = ''; this.loading = false; }, error: () => { this.error = 'No se pudo guardar la observación'; this.loading = false; } }); }
  analyze(item: Observation): void { this.http.post<Observation>(`${API_BASE_URL}/observations/${item.id}/analyze`, {}).subscribe({ next: updated => item = Object.assign(item, updated), error: () => this.error = 'No se pudo analizar la observación' }); }
}

