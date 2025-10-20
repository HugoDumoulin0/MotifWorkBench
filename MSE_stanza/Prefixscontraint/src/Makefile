CC = g++
CFLAGS = -O3 -Wall -ansi -pipe -static -fopenmp 
EXEC=prefixspanseq
EXEC_NAME = ../bin/$(EXEC)
INCLUDES =
OBJ_FILES = forward.o type.o main.o

all : $(EXEC_NAME)

clean :
	rm $(EXEC_NAME) $(OBJ_FILES)

$(EXEC_NAME) : $(OBJ_FILES)
	$(CC) $(CFLAGS) -o  $(EXEC_NAME) $(OBJ_FILES) $(LIBS)

%.o: %.cpp
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ -c $<

%.o: %.cc
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ -c $<

%.o: %.c
	gcc $(CFLAGS) $(INCLUDES) -o $@ -c $<

# install :
# 	cp $(EXEC_NAME) /usr/bin
# 
# uninstall :
# 	rm -f /usr/bin/$(EXEC)
