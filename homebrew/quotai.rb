class Quotai < Formula
  desc "Z.ai quota monitor with terminal and JSON output"
  homepage "https://github.com/soakes/quotai"
  url "https://github.com/soakes/quotai/releases/download/v1.0.1/quotai-1.0.1.tar.gz"
  sha256 "f8cbf0634b3ff0d9d32ecd2fa3affdcce2cf7da16709d727932f5ae6b027e3d9"
  license "MIT"

  depends_on "python@3.10"

  def install
    bin.install "quotai.py" => "quotai"
  end

  test do
    assert_match "usage", shell_output("#{bin}/quotai --help 2>&1", 1)
  end
end
