import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { WhatsAppComponent } from './whatsapp.component';
import { WhatsAppRoutingModule } from './whatsapp-routing.module';

@NgModule({
  declarations: [WhatsAppComponent],
  imports: [CommonModule, FormsModule, WhatsAppRoutingModule],
})
export class WhatsAppModule {}
