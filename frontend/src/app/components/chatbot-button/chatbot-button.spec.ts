import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ChatbotButton } from './chatbot-button';

describe('ChatbotButton', () => {
  let component: ChatbotButton;
  let fixture: ComponentFixture<ChatbotButton>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatbotButton],
    }).compileComponents();

    fixture = TestBed.createComponent(ChatbotButton);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
