describe('WhatsApp inbox', () => {
  beforeEach(() => {
    const cors = { 'Access-Control-Allow-Origin': 'http://127.0.0.1:4300', 'Access-Control-Allow-Credentials': 'true' };
    cy.intercept('GET', 'http://localhost:8000/api/v1/analytics/dashboard', { body: { observations: 0, analyzed: 0, average_price: null, top_models: [], demand_signals: 0, sale_signals: 0 }, headers: cors });
    cy.intercept('GET', 'http://localhost:8000/api/v1/whatsapp/accounts', { body: [], headers: cors });
    cy.intercept('GET', 'http://localhost:8000/api/v1/whatsapp/conversations*', { body: [], headers: cors });
    cy.visit('/auth');
    cy.contains('Ingresar').click();
    cy.contains('a', 'WhatsApp').click();
  });

  it('opens the inbox and explains which conversations it can show', () => {
    cy.contains('h1', 'WhatsApp').should('be.visible');
    cy.contains('Solo conversaciones individuales entregadas a tu cuenta empresarial por Meta. No incluye chats personales ni grupos.').should('be.visible');
  });
});
