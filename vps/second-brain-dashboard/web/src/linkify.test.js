import { describe, expect, it } from "vitest";
import { extractUrls, linkifyParts, toHref } from "./linkify.js";

describe("linkify", () => {
  it("splits https URLs and strips trailing punctuation", () => {
    const parts = linkifyParts(
      "Slack: https://rb-edu.slack.com/archives/C061VU31TUY/p1792746356034809.",
    );
    expect(parts).toEqual([
      { text: "Slack: ", href: null },
      {
        text: "https://rb-edu.slack.com/archives/C061VU31TUY/p1792746356034809",
        href: "https://rb-edu.slack.com/archives/C061VU31TUY/p1792746356034809",
      },
      { text: ".", href: null },
    ]);
  });

  it("linkifies bare domains and www", () => {
    const parts = linkifyParts("dny.ai a www.ai4biz.cz/program");
    expect(parts.map((p) => p.href)).toEqual([
      "https://dny.ai/",
      null,
      "https://www.ai4biz.cz/program",
    ]);
    expect(parts[0].text).toBe("dny.ai");
    expect(parts[2].text).toBe("www.ai4biz.cz/program");
  });

  it("rejects non-http schemes via toHref", () => {
    expect(toHref("javascript:alert(1)")).toBeNull();
    expect(toHref("https://ok.example")).toBe("https://ok.example/");
  });

  it("extractUrls returns unique http(s) links", () => {
    expect(
      extractUrls("RSVP https://no-work.circle.so a znovu https://no-work.circle.so"),
    ).toEqual(["https://no-work.circle.so/"]);
  });
});
