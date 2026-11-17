package eval;

import java.io.*;
import java.nio.channels.*;
import java.nio.file.*;

/** Process-exclusive attempt identity sequence, durable before any MCP request. */
public final class InvocationSequence implements AutoCloseable {
    private final Path path;
    private final FileChannel channel;
    private final FileLock lock;
    private long sequence;
    public InvocationSequence(Path path) throws IOException {
        this.path=path;
        channel=FileChannel.open(path.resolveSibling(path.getFileName()+".lock"),StandardOpenOption.CREATE,StandardOpenOption.WRITE);
        try {
            lock=channel.tryLock();
            if(lock==null) throw new IllegalStateException("Native executor already owns this workspace");
        } catch(RuntimeException error) {channel.close();throw new IllegalStateException("Native writer lock refused",error);}
        try {
            sequence=Files.exists(path)?Long.parseLong(Files.readString(path).strip()):0;
            if(sequence<0) throw new IllegalStateException("Invalid sequence");
        } catch(IOException|RuntimeException error) {lock.close();channel.close();throw error;}
    }
    public synchronized long next() throws IOException {
        if(!lock.isValid()) throw new IllegalStateException("Executor sequence closed");
        long next=Math.addExact(sequence,1);
        Path temporary=Files.createTempFile(path.getParent(),".invocation-",".tmp");
        try {
            Files.writeString(temporary,""+next);
            try(var out=FileChannel.open(temporary,StandardOpenOption.WRITE)) {out.force(true);}
            Files.move(temporary,path,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
            sequence=next;return next;
        } finally {Files.deleteIfExists(temporary);}
    }
    @Override public void close() {
        try {lock.close();channel.close();} catch(IOException error) {throw new UncheckedIOException(error);}
    }
}
