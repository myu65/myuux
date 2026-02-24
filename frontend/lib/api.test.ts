import { describe, expect, it } from "vitest";

import { createUrl } from "./api";

describe("createUrl", () => {
  it("joins API base and path", () => {
    expect(createUrl("/api/workspaces")).toContain("/api/workspaces");
  });
});
