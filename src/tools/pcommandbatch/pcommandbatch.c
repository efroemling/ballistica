// Released under the MIT License. See LICENSE for details.

// An ultra-simple client app to forward commands to a pcommand server. This
// lets us run *lots* of small pcommands very fast. Often the limiting
// factor in such cases is the startup time of Python which this mostly
// eliminates. See tools/efrotools/pcommandbatch.py for more info.

#include <arpa/inet.h>
#include <assert.h>
#include <errno.h>
#include <fcntl.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/param.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>

#include "cJSON.h"

struct Context_ {
  const char* state_dir_path;
  const char* project_dir_path;
  const char* instance_prefix;
  int instance_num;
  int pid;
  int verbose;
  int debug;
  int server_idle_seconds;
  const char* pcommandpath;
  int sockfd;
};

int path_exists_(const char* path);
int establish_connection_(struct Context_* ctx);
int calc_paths_(struct Context_* ctx);
int send_command_(struct Context_* ctx, int argc, char** argv);
int handle_response_(struct Context_* ctx);

// Read all data from a socket and return as a malloc'ed null-terminated
// string.
char* read_string_from_socket_(const struct Context_* ctx);

// Tear down context (closing socket, etc.) before closing app.
void tear_down_context_(struct Context_* ctx);

// If a valid state file is present at the provided path and not older than
// server_idle_seconds, return said port as an int. Otherwise return -1;
int get_running_server_port_(const struct Context_* ctx,
                             const char* state_file_path_full);

int main(int argc, char** argv) {
  struct Context_ ctx;
  memset(&ctx, 0, sizeof(ctx));

  ctx.server_idle_seconds = 5;
  ctx.pid = getpid();
  ctx.sockfd = -1;

  // Verbose mode enables more printing here. Debug mode enables that plus
  // extra stuff. The extra stuff is mostly the server side though.
  {
    const char* debug_env = getenv("BA_PCOMMANDBATCH_DEBUG");
    ctx.debug = debug_env && !strcmp(debug_env, "1");
    const char* verbose_env = getenv("BA_PCOMMANDBATCH_VERBOSE");
    ctx.verbose = ctx.debug || (verbose_env && !strcmp(verbose_env, "1"));
  }

  // Seed rand() using the current time in microseconds.
  struct timeval tv;
  gettimeofday(&tv, NULL);
  unsigned int seed = tv.tv_usec;
  srand(seed);

  // Figure our which file path we'll use to get server state.
  if (calc_paths_(&ctx) != 0) {
    tear_down_context_(&ctx);
    return 1;
  }

  // Establish communication with said server (spinning it up if needed).
  ctx.sockfd = establish_connection_(&ctx);
  if (ctx.sockfd == -1) {
    tear_down_context_(&ctx);
    return 1;
  }

  if (send_command_(&ctx, argc, argv) != 0) {
    tear_down_context_(&ctx);
    return 1;
  }

  int result_val = handle_response_(&ctx);
  if (result_val != 0) {
    tear_down_context_(&ctx);
    return 1;
  }

  tear_down_context_(&ctx);
  return result_val;
}

void tear_down_context_(struct Context_* ctx) {
  if (ctx->sockfd != -1) {
    if (close(ctx->sockfd) != 0) {
      fprintf(stderr,
              "Error: pcommandbatch client %s_%d (pid %d): error %d closing "
              "socket.\n",
              ctx->instance_prefix, ctx->instance_num, ctx->pid, errno);
    }
  }
}

int get_running_server_port_(const struct Context_* ctx,
                             const char* state_file_path_full) {
  struct stat file_stat;

  time_t current_time = time(NULL);
  if (current_time == -1) {
    perror("time");
    return -1;
  }

  int fd = open(state_file_path_full, O_RDONLY);
  if (fd < 0) {
    return -1;
  }

  if (fstat(fd, &file_stat) == -1) {
    close(fd);
    return -1;
  }

  int age_seconds = current_time - file_stat.st_mtime;
  if (ctx->verbose) {
    if (age_seconds <= ctx->server_idle_seconds) {
      fprintf(stderr,
              "pcommandbatch client %s_%d (pid %d) found state file with age "
              "%d at "
              "time %ld.\n",
              ctx->instance_prefix, ctx->instance_num, ctx->pid, age_seconds,
              time(NULL));
    }
  }

  if (age_seconds > ctx->server_idle_seconds) {
    close(fd);
    return -1;
  } else if (age_seconds < 0) {
    fprintf(stderr, "pcommandbatch got negative age; unexpected.");
  }

  char buf[256];
  ssize_t amt = read(fd, buf, sizeof(buf) - 1);
  close(fd);

  if (amt == -1 || amt == sizeof(buf) - 1) {
    return -1;
  }
  buf[amt] = 0;  // Null-terminate it.

  cJSON* state_dict = cJSON_Parse(buf);
  if (!state_dict) {
    fprintf(stderr,
            "Error: pcommandbatch client %s_%d (pid %d): failed to parse state "
            "value.\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid);
    return -1;
  }

  // If results included output, print it.
  cJSON* port_obj = cJSON_GetObjectItem(state_dict, "p");
  if (!port_obj || !cJSON_IsNumber(port_obj)) {
    fprintf(stderr,
            "Error: pcommandbatch client %s_%d (pid %d): failed to get port "
            "value from state.\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid);
    cJSON_Delete(state_dict);
    return -1;
  }
  int port = cJSON_GetNumberValue(port_obj);
  cJSON_Delete(state_dict);
  return port;
}

int path_exists_(const char* path) {
  struct stat file_stat;
  return (stat(path, &file_stat) != -1);
}

int establish_connection_(struct Context_* ctx) {
  char state_file_path_full[256];
  snprintf(state_file_path_full, sizeof(state_file_path_full),
           "%s/worker_state_%s_%d", ctx->state_dir_path, ctx->instance_prefix,
           ctx->instance_num);

  int sockfd = 0;

  if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
    fprintf(stderr,
            "Error: pcommandbatch client %s_%d (pid %d): could not create "
            "socket.\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid);
    return -1;
  }

  // On Mac I'm running into EADDRNOTAVAIL errors if I spit out too many
  // requests in a short enough period of time. I'm guessing its exhausting
  // free ports when cooldown time is taken into account. Sleeping and
  // trying again in a moment seems to work.
  int retry_attempt = 0;
  int retry_sleep_secs = 1;
  while (1) {
    // First look for an already-running batch server.
    int port = get_running_server_port_(ctx, state_file_path_full);
    if (port == -1) {
      // Ok; no running server. Spin one up.
      if (ctx->verbose) {
        fprintf(stderr,
                "pcommandbatch client %s_%d (pid %d) requesting batch server "
                "spinup...\n",
                ctx->instance_prefix, ctx->instance_num, ctx->pid);
      }

      // In non-debug-mode, route to a log file.
      char endbuf[1024];
      if (ctx->debug) {
        snprintf(endbuf, sizeof(endbuf), " &");
      } else {
        snprintf(endbuf, sizeof(endbuf), " >>%s/worker_log_%s_%d 2>&1 &",
                 ctx->state_dir_path, ctx->instance_prefix, ctx->instance_num);
      }
      char buf[2048];
      snprintf(buf, sizeof(buf),
               "%s batchserver --timeout %d --project-dir %s"
               " --instance %s_%d %s",
               ctx->pcommandpath, ctx->server_idle_seconds,
               ctx->project_dir_path, ctx->instance_prefix, ctx->instance_num,
               endbuf);
      system(buf);

      // Spin and wait up to a few seconds for the file to appear.
      time_t start_time = time(NULL);
      int cycles = 0;
      while (time(NULL) - start_time < 5) {
        port = get_running_server_port_(ctx, state_file_path_full);
        if (port != -1) {
          break;
        }
        usleep(10000);
        cycles += 1;
      }
      if (ctx->verbose) {
        fprintf(stderr,
                "pcommandbatch client %s_%d (pid %d) waited %d"
                " cycles for state file to appear at '%s'.\n",
                ctx->instance_prefix, ctx->instance_num, ctx->pid, cycles,
                state_file_path_full);
      }

      if (port == -1) {
        // We failed but we can retry.
        if (ctx->verbose) {
          fprintf(stderr,
                  "Error: pcommandbatch client %s_%d (pid %d): failed to open "
                  "server on attempt %d.\n",
                  ctx->instance_prefix, ctx->instance_num, ctx->pid,
                  retry_attempt);
        }
      }
    }

    // Ok we got a port; now try to connect to it.
    if (port != -1) {
      if (ctx->verbose) {
        fprintf(stderr,
                "pcommandbatch client %s_%d (pid %d) will use server on port "
                "%d at "
                "time %ld.\n",
                ctx->instance_prefix, ctx->instance_num, ctx->pid, port,
                time(NULL));
      }

      struct sockaddr_in serv_addr;
      memset(&serv_addr, '0', sizeof(serv_addr));
      serv_addr.sin_family = AF_INET;
      serv_addr.sin_port = htons(port);
      serv_addr.sin_addr.s_addr = inet_addr("127.0.0.1");

      int cresult =
          connect(sockfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr));
      if (cresult == 0) {
        break;
      } else if (errno == EADDRNOTAVAIL) {
        // Seems we can get this if blasting the machine with enough
        // commands that they run out of ports for us to use. The situation
        // should resolve itself if we wait/retry a few times.
        if (ctx->verbose) {
          fprintf(stderr,
                  "pcommandbatch client %s_%d (pid %d): got EADDRNOTAVAIL"
                  " on connect attempt %d.\n",
                  ctx->instance_prefix, ctx->instance_num, ctx->pid,
                  retry_attempt + 1);
        }
      } else if (errno == ECONNREFUSED) {
        // Am seeing these very rarely on random one-off commands. I'm
        // guessing there's some race condition at the OS level where the
        // port-file write goes through before the socket is actually truly
        // accepting connections. A retry should succeed.
        if (ctx->verbose) {
          fprintf(stderr,
                  "pcommandbatch client %s_%d (pid %d): got ECONNREFUSED"
                  " on connect attempt %d.\n",
                  ctx->instance_prefix, ctx->instance_num, ctx->pid,
                  retry_attempt + 1);
        }
      } else if (errno == EINVAL) {
        // Saw this randomly once on Mac. Not sure what could have led to it.
        if (ctx->verbose) {
          fprintf(stderr,
                  "pcommandbatch client %s_%d (pid %d): got EINVAL"
                  " on connect attempt %d.\n",
                  ctx->instance_prefix, ctx->instance_num, ctx->pid,
                  retry_attempt + 1);
        }
      } else {
        // Currently not retrying on other errors.
        fprintf(stderr,
                "Error: pcommandbatch client %s_%d (pid %d): connect failed "
                "(errno "
                "%d).\n",
                ctx->instance_prefix, ctx->instance_num, ctx->pid, errno);
        close(sockfd);
        return -1;
      }
    }
    // Let's stop at 5, which will be about a minute of waiting total.
    if (retry_attempt >= 5) {
      fprintf(stderr,
              "Error: pcommandbatch client %s_%d (pid %d): too many "
              "retry attempts; giving up.\n",
              ctx->instance_prefix, ctx->instance_num, ctx->pid);
      close(sockfd);
      return -1;
    }

    // Am currently seeing the occasional hang in this loop. Let's flip
    // into verbose if that might be happening to diagnose.
    ctx->verbose = 1;

    if (ctx->verbose) {
      fprintf(
          stderr,
          "pcommandbatch client %s_%d (pid %d) connection attempt %d failed;"
          " will sleep %d secs and try again.\n",
          ctx->instance_prefix, ctx->instance_num, ctx->pid, retry_attempt + 1,
          retry_sleep_secs);
    }
    sleep(retry_sleep_secs);
    retry_attempt += 1;
    retry_sleep_secs *= 2;
  }
  return sockfd;
}

int calc_paths_(struct Context_* ctx) {
  // Because the server needs to be in the same cwd as we are for things to
  // work, we only support a specific few locations to run from. Currently
  // this is project-root and src/assets
  if (path_exists_("config/projectconfig.json")) {
    // Looks like we're in project root.
    ctx->project_dir_path = ".";
    ctx->state_dir_path = ".cache/pcommandbatch";
    ctx->instance_prefix = "root";
    ctx->pcommandpath = "tools/pcommand";
  } else if (path_exists_("ba_data")
             && path_exists_("../../config/projectconfig.json")) {
    // Looks like we're in src/assets.
    ctx->project_dir_path = "../..";
    ctx->state_dir_path = "../../.cache/pcommandbatch";
    ctx->instance_prefix = "assets";
    ctx->pcommandpath = "../../tools/pcommand";
  }
  if (ctx->state_dir_path == NULL) {
    char cwdbuf[MAXPATHLEN];
    if (getcwd(cwdbuf, sizeof(cwdbuf)) < 0) {
      fprintf(stderr,
              "Error: pcommandbatch client %s (pid %d): unable to get cwd.\n",
              ctx->instance_prefix, ctx->pid);
      return -1;
    }
    fprintf(stderr,
            "Error: pcommandbatch client %s (pid %d): pcommandbatch from cwd "
            "'%s' "
            "is not supported.\n",
            ctx->instance_prefix, ctx->pid, cwdbuf);
    return -1;
  }
  assert(ctx->pcommandpath != NULL);
  assert(ctx->instance_prefix != NULL);

  // Spread requests for each location out randomly across a few instances.
  // This greatly increases scalability though is probably wasteful when
  // running just a few commands since we likely spin up a new server for
  // each. Maybe there's some way to smartly scale this. The best setup
  // might be to have a single 'controller' server instance that spins up
  // worker instances as needed. Though such a fancy setup might be
  // overkill.
  // ctx->instance_num = rand() % 6;

  // I was wondering if using pid would lead to a more even distribution,
  // but it didn't make a significant difference in my tests. And I worry
  // there would be some odd corner case where pid isn't going up evenly, so
  // sticking with rand() for now. ctx->instance_num = ctx->pid % 6;

  // Actually I think this might be a good technique. This should deliver a
  // few consecutive requests to a single server instance so it should
  // reduce wasted spinup time when just a command or two is run, but it
  // should still scale up to use all 6 instances when lots of commands go
  // through. (tests show this to be the same speed as the others in that
  // latter case).
  ctx->instance_num = (ctx->pid / 4) % 6;
  return 0;
}

int color_enabled() {
  // This logic here should line up with how the 'color_enabled' val in
  // efro.terminal is calculated.

  // Allow explict enabling/disabling via this env var.
  const char* env = getenv("EFRO_TERMCOLORS");
  if (env && !strcmp(env, "1")) {
    return 1;
  }
  if (env && !strcmp(env, "0")) {
    return 0;
  }

  env = getenv("TERM");

  // If TERM is unset, don't attempt color (this is currently the case
  // in xcode).
  if (!env) {
    return 0;
  }

  // A common way to say the terminal can't do fancy stuff like color.
  if (env && !(strcmp(env, "dumb"))) {
    return 0;
  }

  // If our stdout is not attached to a terminal, go with no-color.
  if (!isatty(1)) {
    return 0;
  }

  // We seem to be a terminal with color support; let's do it!
  return 1;
}

int send_command_(struct Context_* ctx, int argc, char** argv) {
  // Build a json array of our args.
  cJSON* req = cJSON_CreateObject();
  cJSON* array = cJSON_CreateArray();
  for (int i = 0; i < argc; ++i) {
    cJSON_AddItemToArray(array, cJSON_CreateString(argv[i]));
  }
  cJSON_AddItemToObject(req, "a", array);
  cJSON_AddItemToObject(
      req, "c", color_enabled() ? cJSON_CreateTrue() : cJSON_CreateFalse());
  char* json_out = cJSON_Print(req);

  // Send our command.
  int msglen = strlen(json_out);
  if (write(ctx->sockfd, json_out, msglen) != msglen) {
    fprintf(stderr,
            "Error: pcommandbatch client %s_%d (pid %d): write failed.\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid);
    return -1;
  }

  // Issue a write shutdown so they get EOF on the other end.
  if (shutdown(ctx->sockfd, SHUT_WR) < 0) {
    fprintf(stderr,
            "Error: pcommandbatch client %s_%d (pid %d): write shutdown "
            "failed.\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid);
    return -1;
  }

  // Clean up our mess after we've sent them on their way.
  free(json_out);
  cJSON_Delete(req);

  return 0;
}

int handle_response_(struct Context_* ctx) {
  char* inbuf = read_string_from_socket_(ctx);

  // Getting null or an empty string response imply something is broken.
  if (!inbuf || inbuf[0] == 0) {
    fprintf(stderr,
            "Error: pcommandbatch client %s_%d (pid %d): failed to read result "
            "(errno %d).\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid, errno);
    if (inbuf) {
      free(inbuf);
    }
    return -1;
  }

  cJSON* result_dict = cJSON_Parse(inbuf);

  if (!result_dict) {
    fprintf(
        stderr,
        "Error: pcommandbatch client %s_%d (pid %d): failed to parse result "
        "value: %s\n",
        ctx->instance_prefix, ctx->instance_num, ctx->pid, inbuf);
    free(inbuf);
    return -1;
  } else {
    free(inbuf);
  }

  // If results included stdout output, print it.
  cJSON* result_output = cJSON_GetObjectItem(result_dict, "o");
  if (!result_output || !cJSON_IsString(result_output)) {
    fprintf(
        stderr,
        "Error: pcommandbatch client %s_%d (pid %d): failed to parse result "
        "output value.\n",
        ctx->instance_prefix, ctx->instance_num, ctx->pid);
    cJSON_Delete(result_dict);
    return -1;
  }
  char* output_str = cJSON_GetStringValue(result_output);
  assert(output_str);
  if (output_str[0] != 0) {
    printf("%s", output_str);
  }

  // If results included stderr output, print it.
  result_output = cJSON_GetObjectItem(result_dict, "e");
  if (!result_output || !cJSON_IsString(result_output)) {
    fprintf(
        stderr,
        "Error: pcommandbatch client %s_%d (pid %d): failed to parse result "
        "output value.\n",
        ctx->instance_prefix, ctx->instance_num, ctx->pid);
    cJSON_Delete(result_dict);
    return -1;
  }
  output_str = cJSON_GetStringValue(result_output);
  assert(output_str);
  if (output_str[0] != 0) {
    fprintf(stderr, "%s", output_str);
  }

  cJSON* result_code = cJSON_GetObjectItem(result_dict, "r");
  if (!result_code || !cJSON_IsNumber(result_code)) {
    fprintf(
        stderr,
        "Error: pcommandbatch client %s_%d (pid %d): failed to parse result "
        "code value.\n",
        ctx->instance_prefix, ctx->instance_num, ctx->pid);
    cJSON_Delete(result_dict);
    return -1;
  }
  int result_val = cJSON_GetNumberValue(result_code);
  if (ctx->verbose) {
    fprintf(stderr, "pcommandbatch client %s_%d (pid %d) final result is %d.\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid, result_val);
  }
  cJSON_Delete(result_dict);

  return result_val;
}

char* read_string_from_socket_(const struct Context_* ctx) {
  const size_t initial_buffer_size = 1024 * 10;
  char* buffer = NULL;
  size_t buffer_size = 0;
  size_t data_received = 0;

  // Allocate initial memory for the buffer
  buffer = malloc(initial_buffer_size);
  if (!buffer) {
    perror("Failed to allocate memory for buffer");
    return NULL;
  }
  buffer_size = initial_buffer_size;

  while (1) {
    // Read data from the socket.
    ssize_t bytes_read = recv(ctx->sockfd, buffer + data_received,
                              buffer_size - data_received - 1, 0);
    if (bytes_read == -1) {
      perror("Error reading socket data");
      free(buffer);
      return NULL;
    } else if (bytes_read == 0) {
      // Connection closed.
      break;
    }

    data_received += bytes_read;

    // Check if buffer is full (reserving space for term char); resize if
    // necessary.
    if (data_received + 1 >= buffer_size) {
      buffer_size *= 2;
      char* rbuffer = (char*)realloc(buffer, buffer_size);
      if (rbuffer) {
        buffer = rbuffer;
      } else {
        perror("Failed to resize buffer");
        free(buffer);
        return NULL;
      }
    }
  }
  assert(data_received + 1 < buffer_size);
  if (ctx->verbose) {
    fprintf(stderr,
            "pcommandbatch client %s_%d (pid %d) read %zu byte response.\n",
            ctx->instance_prefix, ctx->instance_num, ctx->pid, data_received);
  }

  buffer[data_received] = 0;  // Null terminator.
  return buffer;
}
