"""CPU functionality."""

from datetime import datetime
import msvcrt
import sys


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        # Initialize RAM and Register
        self.ram = [0] * 256
        self.reg = [0] * 8
        # Set original stack pointer
        self.reg[7] = 0xf4
        self.pc = 0
        # This dictionary is not strictly necessary
        # but it's helpful to comprehend what's going on.
        self.dictionary = {
            0b10100000: 'ADD',
            0b10000101: 'ADDI',
            0b10101000: 'AND',
            0b01010000: 'CALL',
            0b10100111: 'CMP',
            0b01100110: 'DEC',
            0b10100011: 'DIV',
            0b00000001: 'HLT',
            0b01100101: 'INC',
            0b01010010: 'INT_',
            0b00010011: 'IRET',
            0b01010101: 'JEQ',
            0b01011010: 'JGE',
            0b01010111: 'JGT',
            0b01011001: 'JLE',
            0b01011000: 'JLT',
            0b01010100: 'JMP',
            0b01010110: 'JNE',
            0b10000011: 'LD',
            0b10000010: 'LDI',
            0b10100100: 'MOD',
            0b10100010: 'MUL',
            0b00000000: 'NOP',
            0b01101001: 'NOT',
            0b10101010: 'OR',
            0b01000110: 'POP',
            0b01001000: 'PRA',
            0b01000111: 'PRN',
            0b01000101: 'PUSH',
            0b00010001: 'RET',
            0b10101100: 'SHL',
            0b10101101: 'SHR',
            0b10000100: 'ST',
            0b10100001: 'SUB',
            0b10101011: 'XOR'
        }
        self.fl = 0b00000000

    def ram_read(self, mar):
        """Returns value stored in the given RAM address"""
        mdr = self.ram[mar]
        return mdr

    def ram_write(self, mdr, mar):
        """Writes a value into RAM at the given address"""
        self.ram[mar] = mdr

    def load(self, filename):
        """Opens file, reads it line by line, and loads them into memory."""

        address = 0

        # For now, we've just hardcoded a program:

        # program = [
        #     # From print8.ls8
        #     0b10000010, # LDI R0,8
        #     0b00000000,
        #     0b00001000,
        #     0b01000111, # PRN R0
        #     0b00000000,
        #     0b00000001, # HLT
        # ]
        with open(filename) as f:
            program = f.readlines()
        for line in program:
            if '#' in line:
                instruction = line.split('#')[0]
            else:
                instruction = line.split('\n')[0]
            if len(instruction) == 0:
                continue
            else:
                #print(f'writing {instruction}')
                instruction = int(instruction, 2)
                self.ram_write(instruction, address)
                address += 1

    def alu(self, op, reg_a, reg_b):
        """ALU operations."""

        if op == "ADD":
            self.reg[reg_a] += self.reg[reg_b]
        elif op == 'AND':
            self.reg[reg_a] = self.reg[reg_a] & self.reg[reg_b]
        elif op == 'CMP':
            if self.reg[reg_a] == self.reg[reg_b]:
                # Set 0th bit of flag to 1, 1st and 2nd bits to 0
                self.fl = self.fl | 0b00000001
                self.fl = self.fl & 0b11111001
            elif self.reg[reg_a] < self.reg[reg_b]:
                # Set 2nd bit of flag to 1, 0th and 1st bits to 0
                self.fl = self.fl | 0b00000100
                self.fl = self.fl & 0b11111100
            else:
                # Set 1st bit of flag to 1, 0th and 2nd bits to 0
                self.fl = self.fl | 0b00000010
                self.fl = self.fl & 0b11111010
        elif op == 'DEC':
            self.reg[reg_a] -= 1
        elif op == 'DIV':
            self.reg[reg_a] = self.reg[reg_a] / self.reg[reg_b]
        elif op == 'INC':
            self.reg[reg_a] += 1
        elif op == 'MOD':
            self.reg[reg_a] = self.reg[reg_a] % self.reg[reg_b]
        elif op == 'MUL':
            self.reg[reg_a] *= self.reg[reg_b]
        elif op == 'NOT':
            self.reg[reg_a] = ~self.reg[reg_a]
        elif op == 'OR':
            self.reg[reg_a] = self.reg[reg_a] | self.reg[reg_b]
        elif op == 'SHL':
            self.reg[reg_a] = self.reg[reg_a] << self.reg[reg_b]
        elif op == 'SHR':
            self.reg[reg_a] = self.reg[reg_a] >> self.reg[reg_b]
        elif op == "SUB":
            self.reg[reg_a] -= self.reg[reg_b]
        elif op == 'XOR':
            self.reg[reg_a] = self.reg[reg_a] ^ self.reg[reg_b]
        else:
            raise Exception("Unsupported ALU operation")
        # Make sure the value in the original is equal to or less than 0xff
        self.reg[reg_a] = self.reg[reg_a] & 0xff

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X %02X | %02X %02X %02X |" % (
            self.pc,
            self.fl,
            #self.ie,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def _decode(self, byte):
        """Decodes byte into the proper instruction string"""
        return self.dictionary[byte]

    def _judge(self, mask, shift=False, shift_amount=None):
        """Judges which bit(s) in the flag is/are activated,
        depending on the mask passed in."""
        self.push(0)
        self.push(1)
        self.ldi(0, self.fl)
        self.ldi(1, mask)
        self.alu('AND', 0, 1)
        if shift:
            self.push(2)
            self.ldi(2, shift_amount)
            self.alu('SHR', 0, 2)
            self.pop(2)
        if self.reg[0] == 0:
            self.pop(1)
            self.pop(0)
            return False
        else:
            self.pop(1)
            self.pop(0)
            return True

    def _check_elapsed_time(self):
        """Checks to see if at least a second has passed
        since the last time an interrupt happened."""
        for i in range(3):
            self.push(i)
        # Save current flag into reserved space in memory,
        # since we'll be overwriting it in this function.
        self.ram_write(self.fl, 0xf6)
        self.ldi(0, 0xf7)
        self.ldi(1, datetime.now().second)
        # Pull previous second amount from 0xf7.
        self.ld(2, 0)
        self.alu('INC', 2, None)
        self.alu('CMP', 1, 2)
        # If the current time is greater or equal to the previous
        # recorded time plus 1, that means at least one second has passed.
        if self._judge(mask=0b00000011):
            self.push(3)
            # Activate 0th bit in R6
            self.ldi(3, 0b00000001)
            self.alu('OR', 6, 3)
            self.pop(3)
            # Store the current time in 0xf7
            self.st(0, 1)
        # Reset the flag to its original value
        self.fl = self.ram_read(0xf6)
        for i in reversed(range(3)):
            self.pop(i)

    def _handle_interrupts(self):
        """Determines if a relevant interrupt occurred, and if
        it did, performs the necessary actions."""
        maskedInterrupts = self.reg[5] & self.reg[6]
        for i in range(8):
            # Right shift interrupts by i, then mask with 1
            if ((maskedInterrupts >> i) & 1) == 1:
                # 1. Disable further interrupts (this will be done later)
                # 2. Clear the bit in the IS register
                is_bit_mask = ''
                for _ in range(abs(7-i)):
                    is_bit_mask += '1'
                is_bit_mask += '0'
                while len(is_bit_mask) < 8:
                    is_bit_mask += '1'
                # Save reg[0] to reserved place in memory
                self.ram_write(self.reg[0], 0xf5)
                self.ldi(0, int(is_bit_mask, 2))
                self.alu('AND', 6, 0)
                # 3. Push PC register onto the stack
                self.ldi(0, self.pc)
                self.push(0)
                # 4. Push FL register onto the stack
                self.ldi(0, self.fl)
                self.push(0)
                # 5. Push registers R0-R6 onto the stack in that order.
                # Bring back original value of reg[0]
                self.reg[0] = self.ram_read(0xf5)
                for j in range(7):
                    self.push(j)
                # 6. Look up vector of the appropriate handler
                vector_address = 0xf8+i
                # 7. Set the PC to (the value stored in the) the vector address
                self.pc = self.ram_read(vector_address)
                # (Disable further interrupts)
                self.ldi(5, 0)
                # Break loop
                break

    def _check_key_press(self):
        """Checks to see if a key has been hit. If it has,
        log the key's value into 0xf4, activate the 1st bit in R6,
        then go through the interrupts process."""
        if msvcrt.kbhit():
            self.ram_write(ord(msvcrt.getch()), 0xf4)
            self.push(0)
            self.ldi(0, 0b00000010)
            self.alu('OR', 6, 0)
            self.pop(0)
            self._handle_interrupts()

    def addi(self, register, imm):
        """Adds an immediate value to a register"""
        if register == 0:
            self.push(1)
            self.ldi(1, imm)
            self.alu('ADD', register, 1)
            self.pop(1)
        else:
            self.push(0)
            self.ldi(0, imm)
            self.alu('ADD', register, 0)
            self.pop(0)

    def call(self, register):
        """Call the function at the RAM address stored in the given register"""
        # Save current value of R) to reserved place in RAM
        self.ram_write(self.reg[0], 0xf5)
        self.ldi(0, self.pc)
        # Add 2 to the PC to get the address of the next instruction
        self.addi(0, 2)
        # Push address of next instruction to stack
        self.push(0)
        # Return R0 to its original value
        self.ldi(0, self.ram_read(0xf5))
        # Set PC to address in given register
        self.pc = self.reg[register]

    def int_(self, register):
        """Issue the interrupt number stored in the given register"""
        # Set the nth bit in the IS register to the value in the given register
        self.alu('OR', 6, register)

    def iret(self):
        """Return from an interrupt handler"""
        # 1. Registers R6-R0 are popped off the stack in that order
        for i in reversed(range(7)):
            self.pop(i)
        # 2. The FL register is popped off the stack
        # Save current value of R0 to reserved space in memory
        self.ram_write(self.reg[0], 0xf5)
        self.pop(0)
        self.fl = self.reg[0]
        # 3. The return address is popped off the stack and stored in PC
        self.pop(0)
        self.pc = self.reg[0]
        # Return original value of R0
        self.ldi(0, self.ram_read(0xf5))
        # 4. Interrupts are re-enabled (this happens automatically
        # since R5 was popped)

    def jeq(self, register):
        """Jumps to the RAM address in the given register if
        the flag's "equal" (0th) bit is activated"""
        if self._judge(mask=0b00000001):
            self.jmp(register)
        else:
            # The PC is not automatically set when this command is called,
            # so if the 0th bit is not activated, we have to set the PC here.
            self.pc += 2

    def jge(self, register):
        """Jumps to the RAM address in the given register if
        the flag's "equal" (0th) or "greater than" (1st) bits are activated"""
        if self._judge(mask=0b00000011):
            self.jmp(register)
        else:
            self.pc += 2

    def jgt(self, register):
        """Jumps to the RAM address in the given register if
        the flag's "greater than" (1st) bit is activated"""
        if self._judge(mask=0b00000010, shift=True, shift_amount=1):
            self.jmp(register)
        else:
            self.pc += 2

    def jle(self, register):
        """Jumps to the RAM address in the given register if
        the flag's "equal" (0th) or "less than" (2nd) bits are activated"""
        if self._judge(mask=0b00000101):
            self.jmp(register)
        else:
            self.pc += 2

    def jlt(self, register):
        """Jumps to the RAM address in the given register if
        the flag's "less than" (2nd) bit is activated"""
        if self._judge(mask=0b00000100, shift=True, shift_amount=2):
            self.jmp(register)
        else:
            self.pc += 2

    def jmp(self, register):
        """Sets the PC to the address in the given register"""
        self.pc = self.reg[register]

    def jne(self, register):
        """Jumps to the RAM address in the given register if
        the flag's "equal" (0th) bit is NOT activated"""
        if not self._judge(mask=0b00000001):
            self.jmp(register)
        else:
            self.pc += 2

    def ld(self, reg_a, reg_b):
        """Loads the value in the RAM address stored in reg_b into reg_a"""
        mar = self.reg[reg_b]
        mdr = self.ram_read(mar)
        self.reg[reg_a] = mdr

    def ldi(self, register, imm):
        """Loads an immediate value into the given register."""
        self.reg[register] = imm

    def nop(self):
        """Not an operation; does nothing"""
        pass

    def pop(self, register):
        """Pops the top value on the stack into the given register"""
        sp = self.reg[7]
        self.reg[register] = self.ram[sp]
        self.alu('INC', 7, None)

    def pra(self, register):
        """Prints the character representation of the value in the given register.
        NOTE: There is no automatic new line printed afterward."""
        print(chr(self.reg[register]), end='', flush=True)
        # Need to set Flush to true so that the print values show up before a new line.

    def prn(self, register):
        """Prints the number in the given register."""
        print(self.reg[register])

    def push(self, register):
        """Pushes the value in the given register onto the stack."""
        self.alu('DEC', 7, None)
        sp = self.reg[7]
        self.ram[sp] = self.reg[register]

    def ret(self):
        """Ends a function call; returns the PC to its original location."""
        # Save current value of R0 to reserved place in RAM
        self.ram_write(self.reg[0], 0xf5)
        # Pop value from top of stack
        self.pop(0)
        # Set that value as the PC
        self.pc = self.reg[0]
        # Return R0 to its previous state
        self.reg[0] = self.ram_read(0xf5)

    def st(self, reg_a, reg_b):
        """Stores the value in reg_a into the RAM location in reg_b."""
        mar = self.reg[reg_a]
        mdr = self.reg[reg_b]
        self.ram_write(mdr, mar)

    def run(self):
        """Run the CPU."""
        self.ram_write(datetime.now().second, 0xf7)
        while True:
            self._check_key_press()
            self._check_elapsed_time()
            if self.reg[6] == 1:
               self._handle_interrupts()
            ir = self.ram_read(self.pc)
            inst = self._decode(ir)
            operand_a = self.ram_read(self.pc+1)
            operand_b = self.ram_read(self.pc+2)

            # This helped to learn how to isolate values in a bit:
            # https://stackoverflow.com/a/45221136/12685847
            # Isolate first two values to get the number of operands
            self.push(0)
            self.push(1)
            self.ldi(0, ir)
            self.ldi(1, 6)
            self.alu('SHR', 0, 1)
            self.ldi(1, 0b00000011)
            self.alu('AND', 0, 1)
            num_ops = self.reg[0]
            # Isolate the 3rd value to see if it's an ALU op
            self.ldi(0, ir)
            self.ldi(1, 5)
            self.alu('SHR', 0, 1)
            self.ldi(1, 0b00000001)
            self.alu('AND', 0, 1)
            is_alu = self.reg[0] 
            # Isolate the 4th value to see if the op sets the PC
            self.ldi(0, ir)
            self.ldi(1, 4)
            self.alu('SHR', 0, 1)
            self.ldi(1, 0b00000001)
            self.alu('AND', 0, 1)
            inst_sets_pc = self.reg[0]
            # Determine the location of the next instruction
            self.ldi(0, self.pc)
            self.ldi(1, num_ops)
            self.alu('INC', 1, None)
            self.alu('ADD', 0, 1)
            next_inst_loc = self.reg[0]
            self.pop(1)
            self.pop(0)

            if inst == 'HLT':
                self.pc = next_inst_loc
                break
            elif is_alu:
                self.alu(inst, operand_a, operand_b)
            else:
                func = getattr(self, inst.lower())
                if num_ops == 0:
                    func()
                elif num_ops == 1:
                    func(operand_a)
                else:
                    func(operand_a, operand_b)

            if not inst_sets_pc:
                self.pc = next_inst_loc
