package eval;

/** No network: enforce the experiment's model transport conditions. */
public final class ModelConfigSelfTest {
    public static void main(String[] args) {
        var config = DeepAgentBridge.modelClientConfig("dummy", "https://example.invalid/v1", 120);
        if (config.getMaxRetries() != 0) throw new AssertionError("Automatic retries must be disabled");
        if (config.getTimeout() != 120) throw new AssertionError("Request timeout differs from manifest");
        if (!config.isVerifySsl()) throw new AssertionError("TLS verification disabled");
        System.out.println("PASS explicit model timeout, zero SDK retries, TLS verification; model_calls=0");
    }
}
