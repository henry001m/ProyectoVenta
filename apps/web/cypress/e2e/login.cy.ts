describe('Kicks Insight', () => {
  it('shows the login screen', () => {
    cy.visit('/auth/login');
    cy.contains('Kicks Insight').should('be.visible');
    cy.contains('Ingresar').should('be.visible');
  });
});
