const std = @import("std");
const net = std.net;
const stdout = std.io.getStdOut().writer();
const eql = std.mem.eql;
const alloc = std.heap.c_allocator;
const readInt = std.mem.readInt;
const Endian = std.builtin.Endian;
const Allocator = std.mem.Allocator;
const ArrayList = std.ArrayList;

pub fn main() !void {
    // initialize server on port 44818 (message port)
    var server = net.StreamServer.init(.{
        .reuse_address = true,
        .reuse_port = true,
    });
    defer {
        server.close();
        server.deinit();
    }
    const address = try net.Address.resolveIp("0.0.0.0", 44818);
    try server.listen(address);
    var buffer: [1024]u8 = undefined;
    var bots = BotManager{};

    try stdout.print("[INFO] Server listening on {}\n", .{server.listen_address});
    while (true) {
        const cn = try server.accept();

        const bytes = try cn.stream.read(&buffer);
        var bot: u8 = undefined;
        var msg = ArrayList(u8).init(alloc);
        var msg_writer = msg.writer();
        defer msg.deinit();
        if (bytes == 3) {
            if (eql(u8, "reb", buffer[0..3])) {
                bot = try bots.addBot();
                try msg_writer.writeAll("r@");
                try msg_writer.writeByte(bot);
                try cn.stream.writeAll(try msg.toOwnedSlice());
                try stdout.print("[INFO] Bot {d} Connected\n", .{bot});
            } else {
                try stdout.print("[WARN] Unknown Request Made\n", .{});
            }
        } else {
            bot = buffer[0];
            if (eql(u8, "loc:", buffer[1..5])) {
                try bots.setLoc(bot, Vec3{ .x = @as(f32, @bitCast(readInt(u32, buffer[5..9], .Little))), .y = @as(f32, @bitCast(readInt(u32, buffer[9..13], .Little))), .z = @as(f32, @bitCast(readInt(u32, buffer[13..17], .Little))) });
                try stdout.print("[INFO] Bot {d} location changed to ({d},{d})\n", .{ bot, bots.bots[bot].loc.x, bots.bots[bot].loc.y });
                try cn.stream.writeAll("ack");
            } else if (eql(u8, "get", buffer[1..4])) {
                try stdout.print("[INFO] Bot {d} requested task\n", .{bot});
                bots.bots[bot].task = .DONE;
                try msg_writer.writeByte(@intFromEnum(bots.bots[bot].task));
                try cn.stream.writeAll(try msg.toOwnedSlice());
            } else if (eql(u8, "fal", buffer[1..4])) {
                try stdout.print("[WARN] Bot {d} failed at task {s}\n", .{ bot, @tagName(bots.bots[bot].task) });
            } else if (eql(u8, "suc", buffer[1..4])) {
                try stdout.print("[INFO] Bot {d} succeeded at assigned task\n", .{bot});
            } else {
                try stdout.print("[WARN] Unknow Request Made\n", .{});
                try cn.stream.writeAll("unk");
            }
        }
    }
}

const BotManager = struct {
    bots: [10]Robot = undefined,
    count: u8 = 0,
    fn addBot(self: *BotManager) !u8 {
        if (self.count == 10) return error.ToManyRobots;
        self.bots[self.count] = .{};
        defer self.count += 1;
        return self.count;
    }
    fn setLoc(self: *BotManager, bot: u8, loc: Vec3) !void {
        if (bot > 10) return error.BotOutOfBounds;
        self.bots[bot].loc = loc;
    }
};
const Robot = struct {
    loc: Vec3 = .{},
    task: Task = .INIT,
};
const Task = enum(u8) { IDLE = 0, MOVING = 1, COLLECT = 2, RETURN = 3, DONE = 4, ERROR = 5, INIT = 6 };
const Vec2 = struct { x: i16 = 0, y: i16 = 0 };
const Vec3 = struct { x: f32 = 0, y: f32 = 0, z: f32 = 0 };
