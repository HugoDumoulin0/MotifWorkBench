CC = clang++
CFLAGS = -O3 -Wall -std=gnu++11 -pipe -Xpreprocessor -fopenmp
LDFLAGS = -lomp
EXEC=bidespantree
EXEC_NAME = ../bin/$(EXEC)
INCLUDES =
OBJ_FILES = forward.o backward.o type.o main.o

HOMEBREW_PREFIX := $(shell brew --prefix 2>/dev/null)
ifneq ($(HOMEBREW_PREFIX),)
INCLUDES += -I$(HOMEBREW_PREFIX)/opt/libomp/include
LDFLAGS += -L$(HOMEBREW_PREFIX)/opt/libomp/lib
endif

all : $(EXEC_NAME)

clean :
	rm -f $(EXEC_NAME) $(OBJ_FILES)

$(EXEC_NAME) : $(OBJ_FILES)
	$(CC) $(CFLAGS) -o  $(EXEC_NAME) $(OBJ_FILES) $(LDFLAGS)

%.o: %.cpp
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ -c $<

%.o: %.cc
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ -c $<

%.o: %.c
	gcc $(CFLAGS) $(INCLUDES) -o $@ -c $<

# Prérequis macOS : brew install libomp