import { Component } from '@angular/core';

@Component({ selector: 'ki-sources', standalone: false, templateUrl: './sources.component.html' })
export class SourcesComponent { readonly sources = [{ name: 'Importación manual', status: 'Disponible' }, { name: 'WhatsApp Business', status: 'Configurable' }, { name: 'TikTok', status: 'OAuth pendiente' }, { name: 'Meta Business', status: 'OAuth pendiente' }]; }

