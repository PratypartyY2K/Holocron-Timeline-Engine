type PageFeedbackProps = {
  title: string;
  message: string;
};

export function LoadingPageFeedback({ title, message }: PageFeedbackProps) {
  return (
    <main className="page-shell">
      <section className="timeline-shell">
        <header className="timeline-header">
          <div>
            <p className="section-kicker">Loading</p>
            <h2>{title}</h2>
          </div>
        </header>
        <p className="detail-empty">{message}</p>
      </section>
    </main>
  );
}

export function ErrorPageFeedback({ title, message }: PageFeedbackProps) {
  return (
    <main className="page-shell">
      <section className="timeline-shell">
        <header className="timeline-header">
          <div>
            <p className="section-kicker">Request error</p>
            <h2>{title}</h2>
          </div>
        </header>
        <p className="detail-empty">{message}</p>
      </section>
    </main>
  );
}
